import functools
import os
import shutil
import subprocess
import sys

from .import plugins
from .config import Config
from .exceptions import (
    ConfigError,
    CouldNotFindPythonError,
    FrozenEnvironmentError,
    NoConfigError,
)


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


def get_config_plugins(config, has_attr=None):
    plugins_list = config['general']['plugins']
    return plugins.get_plugins(
        filter_names=plugins_list,
        has_attr=has_attr
    )


def get_config(startdir=None):
    config = Config.load(startdir)

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
