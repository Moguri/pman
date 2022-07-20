import fnmatch
import functools
import os
import shlex
import shutil
import subprocess
import sys
import time


from . import creationutils
from .exceptions import CouldNotFindPythonError, FrozenEnvironmentError, NoConfigError
from .config import ConfigDict


def get_config(startdir=None):
    config = ConfigDict.load(startdir)
    user_layer = config.layers['user']

    if 'python' not in user_layer:
        user_layer['python'] = {}

    if 'path' not in user_layer['python']:
        user_layer['python']['path'] = ''

    confpy = config['python']['path']
    if not confpy:
        # Try to find a Python program to default to
        try:
            pyprog = get_python_program()
            pyloc = shutil.which(pyprog)
            user_layer['python']['path'] = pyloc
        except CouldNotFindPythonError:
            pass

    return config


def config_exists(startdir=None):
    try:
        get_config(startdir)
        have_config = True
    except NoConfigError:
        have_config = False

    return have_config


def get_user_config(startdir=None):
    '''Compatibility alias, use get_config() instead'''
    return get_config(startdir)


def ensure_config(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        has_config = (
            len(args) > 0 and args[0] is not None or
            'config' in kwargs and kwargs['config'] is not None
        )
        if not has_config:
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


@disallow_frozen
def create_project(projectdir='.', extras=None):
    if not os.path.exists(projectdir):
        os.makedirs(projectdir)

    confpath = os.path.join(projectdir, '.pman')
    if os.path.exists(confpath):
        print(f'Updating project in {projectdir}')
    else:
        print(f'Creating new project in {projectdir}')

    if not os.path.exists(confpath):
        # Touch config file to make sure it is present
        with open(confpath, 'a') as _:
            pass

    config = get_config(projectdir)

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

    if extras:
        import pkg_resources
        entrypoints = {
            entrypoint.name: entrypoint.load()
            for entrypoint in pkg_resources.iter_entry_points('pman.creation_extras')
        }
        for extra in extras:
            if extra not in entrypoints:
                print(f'Could not find creation extra: {extra}')
                continue
            entrypoints[extra](projectdir, config)



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
def build(config=None):
    verbose = config['general']['verbose']
    import pkg_resources
    converters = [
        entry_point.load()
        for entry_point in pkg_resources.iter_entry_points('pman.converters')
        if entry_point.name in config['build']['converters']
    ]

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

    if os.path.exists(srcdir) and os.path.isdir(srcdir):
        # Gather files and group by extension
        ext_asset_map = {}
        ext_dst_map = {}
        ext_converter_map = {}
        for converter in converters:
            ext_dst_map.update(converter.ext_dst_map)
            for ext in converter.supported_exts:
                ext_converter_map[ext] = converter

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
        convert_hooks = []
        for ext, converter in ext_converter_map.items():
            if ext in ext_asset_map:
                convert_hooks.append((converter, ext_asset_map[ext]))
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
        for convert_hook in convert_hooks:
            print('Converting files:')
            for fname in convert_hook[1]:
                print(f'\t{fname}')
            convert_hook[0](config, srcdir, dstdir, convert_hook[1])
    else:
        print(f'warning: could not find asset directory: {srcdir}')


    print(f'Build took {time.perf_counter() - stime:.4f}s')


@ensure_config
@disallow_frozen
def run(config=None):
    mainfile = get_abs_path(config, config['run']['main_file'])
    print(f'Running main file: {mainfile}')
    args = [mainfile] + shlex.split(config['run']['extra_args'])
    run_script(config, args, cwd=config['internal']['projectdir'])


@ensure_config
@disallow_frozen
def dist(config=None, build_installers=True, platforms=None):
    args = [
        'setup.py',
    ]

    if build_installers:
        args += ['bdist_apps']
    else:
        args += ['build_apps']

    if platforms is not None:
        args += ['-p', '{}'.format(','.join(platforms))]

    run_script(config, args, cwd=config['internal']['projectdir'])


@ensure_config
@disallow_frozen
def clean(config=None):
    export_dir = config['build']['export_dir']
    shutil.rmtree(get_abs_path(config, export_dir), ignore_errors=True)
    shutil.rmtree(get_abs_path(config, 'build'), ignore_errors=True)
    shutil.rmtree(get_abs_path(config, 'dist'), ignore_errors=True)
