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
            'show_all_jobs': False,
            'jobs': 0,
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

    PROJECT_CONFIG_NAMES = [
        'pyproject.toml',
        '.pman',
        '.pman.user',
    ]
    DEFAULT_PLUGINS = [
        'native2bam',
        'blend2bam',
    ]

    def __init__(self, config_files):
        confs = []
        for confpath in config_files:
            with (open(confpath, 'rb')) as conffile:
                conf = toml.load(conffile)
                if 'tool' in conf and 'pman' in conf['tool']:
                    conf = conf['tool']['pman']
                confs.append(conf)

        plugins_list = [
            conf['general']['plugins']
            for conf in confs
            if 'general' in conf and 'plugins' in conf['general']
        ]
        if plugins_list:
            plugins_list = plugins_list[-1]
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
            *confs,
            {
                'internal': {
                    'projectdir': os.path.dirname(config_files[0]),
                },
            },
        ]))

    @classmethod
    def load(cls, startdir):
        try:
            if startdir is None:
                startdir = os.getcwd()
        except FileNotFoundError as exc:
            # The project folder was deleted on us
            raise NoConfigError("Could not find config file") from exc

        dirs = os.path.abspath(startdir).split(os.sep)

        while dirs:
            cdir = os.sep.join(dirs)
            if not cdir.strip():
                dirs.pop()
                continue

            foundcfg = set(cls.PROJECT_CONFIG_NAMES) & set(os.listdir(cdir))
            if foundcfg:
                cfgpaths = [
                    os.path.join(cdir, cfgname)
                    for cfgname in cls.PROJECT_CONFIG_NAMES
                    if cfgname in foundcfg
                ]
                return cls(cfgpaths)

            dirs.pop()

        # No config found
        raise NoConfigError("Could not find config file")
