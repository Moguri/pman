import contextlib
import os
import shlex
import shutil

import tomli as toml

from . import creationutils
from ._build import build
from ._utils import (
    disallow_frozen,
    ensure_config,
    get_abs_path,
    get_config,
    get_config_plugins,
    run_hooks,
    run_script,
)


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
        plugin.pre_create(config)

    creationutils.create_dirs(projectdir, (
        config['build']['asset_dir'],
        'tests',
    ))


    templatedir = creationutils.get_template_dir()
    creationutils.copy_template_files(projectdir, templatedir, (
        ('main.py', config['run']['main_file']),
        ('pyproject.toml', 'pyproject.toml'),
        ('test_imports.py', 'tests/test_imports.py'),
    ))

    for plugin in get_config_plugins(config, 'post_create'):
        plugin.post_create(config)


@ensure_config
@disallow_frozen
@run_hooks
def run(config=None):
    mainfile = get_abs_path(config, config['run']['main_file'])
    print(f'Running main file: {mainfile}')
    args = [mainfile, *shlex.split(config['run']['extra_args'])]
    run_script(config, args, cwd=config['internal']['projectdir'])


@ensure_config
@disallow_frozen
@run_hooks
def dist(config=None, build_installers=None, platforms=None):
    verbose = config['general']['verbose']

    build(config)

    pyproject_path = get_abs_path(config, 'pyproject.toml')
    setup_py_path = get_abs_path(config, 'setup.py')
    requirements_path = get_abs_path(config, 'requirements.txt')

    auto_deps = []
    remove_requirements_txt = False
    setup_py_opts = {}
    remove_setup_py = False

    if os.path.exists(pyproject_path):
        with open(pyproject_path, 'rb') as conffile:
            conf = toml.load(conffile)

            auto_deps.extend(conf
                             .get('project', {})
                             .get('dependencies', []))

            setup_py_opts = (conf
                             .get('tool', {})
                             .get('pman', {})
                             .get('build_apps', {}))

    if auto_deps and not os.path.exists(requirements_path):
        # Auto-generate requirements.txt from pyproject.toml
        if verbose:
            print('Generating requirements.txt from pyproject.toml')
        remove_requirements_txt = True
        with open(requirements_path, 'w') as reqfile:
            for dep in auto_deps:
                reqfile.write(f'{dep}\n')

    if setup_py_opts and not os.path.exists(setup_py_path):
        # Auto-generate stub setup.py
        if verbose:
            print('Generating setup.py from pyproject.toml')
        remove_setup_py = True
        with open(setup_py_path, 'w') as setupfile:
            setupfile.write('from setuptools import setup\nsetup(options={\n')
            setupfile.write(f"'build_apps': {setup_py_opts}")
            setupfile.write('\n})')

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
        args += ['-p', f'{",".join(platforms)}']

    try:
        run_script(config, args, cwd=config['internal']['projectdir'])
    finally:
        if remove_requirements_txt:
            os.remove(requirements_path)
        if remove_setup_py:
            os.remove(setup_py_path)

@ensure_config
@disallow_frozen
@run_hooks
def clean(config=None):
    export_dir = config['build']['export_dir']
    shutil.rmtree(get_abs_path(config, export_dir), ignore_errors=True)
    shutil.rmtree(get_abs_path(config, 'build'), ignore_errors=True)
    shutil.rmtree(get_abs_path(config, 'dist'), ignore_errors=True)
    with contextlib.suppress(FileNotFoundError):
        os.unlink(get_abs_path(config, '.pman_builddb'))
