import collections
import functools
import os
import tomli as toml


from . import plugins
from .exceptions import NoConfigError


def _merge_dict(dst: dict, src: dict):
    for key, value in src.items():
        if isinstance(value, dict):
            _merge_dict(dst.setdefault(key, {}), value)
        else:
            dst[key] = value

    return dst

class ConfigDict(collections.UserDict):
    '''Extend ChainMap to provide a config object with overlays'''

    _CONFIG_DEFAULTS = {
        'general': {
            'name': 'Game',
            'verbose': False,
            'plugins': ['DefaultPlugins'],
        },
        'build': {
            'asset_dir': 'assets/',
            'export_dir': '.built_assets/',
            'ignore_patterns': ['*.blend1', '*.blend2'],
        },
        'run': {
            'main_file': 'main.py',
            'extra_args': '',
            'auto_build': True,
            'auto_save': True,
        },
        'dist': {
            'build_installers': True,
        },
        'python': {
            'path': '',
        },
    }

    PROJECT_CONFIG_NAME = '.pman'
    USER_CONFIG_NAME = f'{PROJECT_CONFIG_NAME}.user'
    DEFAULT_PLUGINS = [
        'native2bam',
        'blend2bam',
    ]

    def __init__(self, project_conf_file, user_conf_file):
        with open(project_conf_file, 'rb') as conffile:
            project_conf = toml.load(conffile)
        user_conf = {}
        if os.path.exists(user_conf_file):
            with open(user_conf_file, 'rb') as conffile:
                user_conf = toml.load(conffile)

        if 'general' in user_conf and 'plugins' in user_conf['general']:
            plugins_list = user_conf['general']['plugins']
        elif 'general' in project_conf and 'plugins' in project_conf['general']:
            plugins_list = project_conf['general']['plugins']
        else:
            plugins_list = self._CONFIG_DEFAULTS['general']['plugins']

        try:
            defult_plugins_loc = plugins_list.index('DefaultPlugins')
            plugins_list[defult_plugins_loc:defult_plugins_loc+1] = self.DEFAULT_PLUGINS
        except ValueError:
            pass

        plist = plugins.get_plugins(filter_names=plugins_list)

        config_defaults = functools.reduce(_merge_dict, [
            getattr(plugin, 'CONFIG_DEFAULTS', {})
            for plugin in plist
        ], self._CONFIG_DEFAULTS)

        super().__init__(functools.reduce(_merge_dict, [
            {},
            config_defaults,
            project_conf,
            user_conf,
            {
                'internal': {
                    'projectdir': os.path.dirname(project_conf_file),
                },
            },
        ]))

    @classmethod
    def load(cls, startdir):
        try:
            if startdir is None:
                startdir = os.getcwd()
        except FileNotFoundError:
            # The project folder was deleted on us
            raise NoConfigError("Could not find config file")

        dirs = os.path.abspath(startdir).split(os.sep)

        while dirs:
            cdir = os.sep.join(dirs)
            if cdir.strip() and cls.PROJECT_CONFIG_NAME in os.listdir(cdir):
                project_conf_file = os.path.join(cdir, cls.PROJECT_CONFIG_NAME)
                user_conf_file = project_conf_file.replace(
                    cls.PROJECT_CONFIG_NAME,
                    cls.USER_CONFIG_NAME,
                )


                return cls(project_conf_file, user_conf_file)

            dirs.pop()

        # No config found
        raise NoConfigError("Could not find config file")
