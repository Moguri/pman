import fnmatch
import functools
import os
import shlex
import shutil
import subprocess
import sys
import time


from . import creationutils
from . import plugins
from .exceptions import CouldNotFindPythonError, FrozenEnvironmentError, NoConfigError, ConfigError
from .config import ConfigDict


def get_config_plugins(config, has_attr=None):
    plugins_list = config['general']['plugins']
    return plugins.get_plugins(
        filter_names=plugins_list,
        has_attr=has_attr
    )


def get_config(startdir=None):
    config = ConfigDict.load(startdir)

    confpy = config['python']['path']
    if not confpy:
        # Try to find a Python program to default to
        try:
            pyprog = get_python_program()
            pyloc = shutil.which(pyprog)
            config['python']['path'] = pyloc
        except CouldNotFindPythonError:
            pass

    plist = get_config_plugins(config)
    found_plugins = [i.name for i in plist]
    for plugname in config['general']['plugins']:
        if plugname not in found_plugins:
            raise ConfigError(f'Failed to load requested plugin: {plugname}')

    return config


def config_exists(startdir=None):
    try:
        get_config(startdir)
        have_config = True
    except NoConfigError:
        have_config = False

    return have_config


def _config_from_args(args, kwargs):
    if len(args) > 0:
        return args[0]
    return kwargs.get('config', None)


def ensure_config(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        config = _config_from_args(args, kwargs)
        if not config:
            kwargs['config'] = get_config()
        return func(*args, **kwargs)
    return wrapper


def is_frozen():
    return getattr(sys, 'frozen', False)


def disallow_frozen(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if is_frozen():
            raise FrozenEnvironmentError()
        return func(*args, **kwargs)
    return wrapper


def run_hooks(func):
    prehook_name = f'pre_{func.__name__}'
    posthook_name = f'post_{func.__name__}'
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        config = _config_from_args(args, kwargs)
        prehooks = get_config_plugins(config, prehook_name)
        posthooks = get_config_plugins(config, posthook_name)

        for plugin in prehooks:
            getattr(plugin, prehook_name)(config)
        retval = func(*args, **kwargs)
        for plugin in posthooks:
            getattr(plugin, posthook_name)(config)
        return retval
    return wrapper


@disallow_frozen
def create_project(projectdir='.', extra_plugins=None):
    if not os.path.exists(projectdir):
        os.makedirs(projectdir)

    confpath = os.path.join(projectdir, '.pman')
    if os.path.exists(confpath):
        print(f'Updating project in {projectdir}')
        config = get_config(projectdir)
        if extra_plugins:
            config['general']['plugins'].extend(extra_plugins)
    else:
        print(f'Creating new project in {projectdir}')

        # Create config file
        with open(confpath, 'w') as conffile:
            if extra_plugins:
                if 'DefaultPlugins' not in extra_plugins:
                    extra_plugins.insert(0, 'DefaultPlugins')
                conffile.write('[general]\n')
                conffile.write(f'plugins = {extra_plugins}\n')
        config = get_config(projectdir)

    for plugin in get_config_plugins(config, 'pre_create'):
        getattr(plugin, 'pre_create')(config)

    creationutils.create_dirs(projectdir, (
        config['build']['asset_dir'],
        'tests',
    ))


    templatedir = creationutils.get_template_dir()
    creationutils.copy_template_files(projectdir, templatedir, (
        ('main.py', config['run']['main_file']),
        ('settings.prc', 'settings.prc'),
        ('requirements.txt', 'requirements.txt'),
        ('setup.py', 'setup.py'),
        ('setup.cfg', 'setup.cfg'),
        ('pylintrc', '.pylintrc'),
        ('test_imports.py', 'tests/test_imports.py'),
    ))

    for plugin in get_config_plugins(config, 'pre_post'):
        getattr(plugin, 'pre_post')(config)



def get_abs_path(config, path):
    return os.path.join(
        config['internal']['projectdir'],
        path
    )


def get_rel_path(config, path):
    return os.path.relpath(path, config['internal']['projectdir'])


def get_python_program(config=None):
    python_programs = [
        'ppython',
        'python3',
        'python',
        'python2',
    ]

    if config is not None:
        confpy = config['python']['path']
        if confpy:
            python_programs.insert(0, confpy)

    # Check to see if there is a version of Python that can import panda3d
    for pyprog in python_programs:
        args = [
            pyprog,
            '-c',
            'import panda3d.core; import direct',
        ]
        try:
            retcode = subprocess.call(args, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            retcode = 1

        if retcode == 0:
            return pyprog

    # We couldn't find a python program to run
    raise CouldNotFindPythonError('Could not find a Python version with Panda3D installed')


def run_program(_config, args, cwd=None):
    subprocess.call(args, cwd=cwd)


def run_script(config, args, cwd=None):
    pyprog = get_python_program(config)
    run_program(config, [pyprog] + args, cwd=cwd)


def converter_copy(_config, srcdir, dstdir, assets):
    for asset in assets:
        src = asset
        dst = src.replace(srcdir, dstdir)
        if not os.path.exists(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        shutil.copyfile(src, dst)


@ensure_config
@disallow_frozen
@run_hooks
def build(config=None):
    verbose = config['general']['verbose']
    converters = plugins.get_converters(config['general']['plugins'])

    stime = time.perf_counter()
    print('Starting build')

    srcdir = get_abs_path(config, config['build']['asset_dir'])
    dstdir = get_abs_path(config, config['build']['export_dir'])

    if verbose:
        print(f'Read assets from: {srcdir}')
        print(f'Export them to: {dstdir}')

    ignore_patterns = config['build']['ignore_patterns']

    if verbose:
        print(f'Ignoring file patterns: {ignore_patterns}')

    if not os.path.exists(dstdir):
        print(f'Creating asset export directory at {dstdir}')
        os.makedirs(dstdir)


    if not os.path.exists(srcdir) or not os.path.isdir(srcdir):
        print(f'warning: could not find asset directory: {srcdir}')
        return

    # Gather files and group by extension
    ext_asset_map = {}
    ext_dst_map = {}
    ext_converter_map = {}
    for converter in converters:
        ext_dst_map.update({
            ext: converter.output_extension
            for ext in converter.supported_extensions
        })
        for ext in converter.supported_extensions:
            ext_converter_map[ext] = converter.function

    for root, _dirs, files in os.walk(srcdir):
        for asset in files:
            src = os.path.join(root, asset)
            dst = src.replace(srcdir, dstdir)

            ignore_pattern = None
            asset_path = src.replace(srcdir, '')
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(asset_path, pattern) or fnmatch.fnmatch(asset, pattern):
                    ignore_pattern = pattern
                    break
            if ignore_pattern is not None:
                if verbose:
                    print(
                        f'Skip building file {asset_path} that '
                        f'matched ignore pattern {ignore_pattern}'
                    )
                continue

            ext = '.' + asset.split('.', 1)[1]

            if ext in ext_dst_map:
                dst = dst.replace(ext, ext_dst_map[ext])

            if os.path.exists(dst) and os.stat(src).st_mtime <= os.stat(dst).st_mtime:
                if verbose:
                    print(f'Skip building up-to-date file: {dst}')
                continue

            if ext not in ext_asset_map:
                ext_asset_map[ext] = []

            ext_asset_map[ext].append(os.path.join(root, asset))

    # Find which extensions have hooks available
    convert_functions = []
    for ext, converter in ext_converter_map.items():
        if ext in ext_asset_map:
            convert_functions.append((converter, ext_asset_map[ext]))
            del ext_asset_map[ext]

    # Copy what is left
    copying_fnames = [
        fname
        for fname_list in ext_asset_map.values()
        for fname in fname_list
    ]
    if copying_fnames:
        print('Copying files:')
        for fname in copying_fnames:
            print(f'\t{fname}')
    for ext in ext_asset_map:
        converter_copy(config, srcdir, dstdir, ext_asset_map[ext])

    # Now run hooks that non-converted assets are in place (copied)
    for convert_function, assets in convert_functions:
        print('Converting files:')
        for fname in assets:
            print(f'\t{fname}')
        convert_function(config, srcdir, dstdir, assets)


    print(f'Build took {time.perf_counter() - stime:.4f}s')


@ensure_config
@disallow_frozen
@run_hooks
def run(config=None):
    mainfile = get_abs_path(config, config['run']['main_file'])
    print(f'Running main file: {mainfile}')
    args = [mainfile] + shlex.split(config['run']['extra_args'])
    run_script(config, args, cwd=config['internal']['projectdir'])


@ensure_config
@disallow_frozen
@run_hooks
def dist(config=None, build_installers=None, platforms=None):
    build(config)

    args = [
        'setup.py',
    ]

    if build_installers is None:
        build_installers = config['dist']['build_installers']

    if build_installers:
        args += ['bdist_apps']
    else:
        args += ['build_apps']

    if platforms is not None:
        args += ['-p', '{}'.format(','.join(platforms))]

    run_script(config, args, cwd=config['internal']['projectdir'])


@ensure_config
@disallow_frozen
@run_hooks
def clean(config=None):
    export_dir = config['build']['export_dir']
    shutil.rmtree(get_abs_path(config, export_dir), ignore_errors=True)
    shutil.rmtree(get_abs_path(config, 'build'), ignore_errors=True)
    shutil.rmtree(get_abs_path(config, 'dist'), ignore_errors=True)
