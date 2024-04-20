import functools
import os
from dataclasses import (
    dataclass,
    field,
    fields,
    is_dataclass,
)
from typing import (
    Any,
    ClassVar,
)

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


def dataclass_from_dict(dataclass_type, data):
    def value_for_field(field_obj):
        val = data[field_obj.name]
        if is_dataclass(field_obj.type):
            return dataclass_from_dict(field_obj.type, val)
        return val

    kwargs = {
        field.name: value_for_field(field)
        for field in fields(dataclass_type)
        if field.name in data
    }

    return dataclass_type(**kwargs)

class ConfigBase:
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __contains__(self, key):
        return hasattr(self, key)


@dataclass
class GeneralConfig(ConfigBase):
    DEFAULT_PLUGINS: ClassVar[list[str]] = [
        'native2bam',
        'blend2bam',
    ]

    name: str = 'Game'
    verbose: bool = False
    plugins: list[str] = field(default_factory=lambda: ['DefaultPlugins'])

    def __post_init__(self) -> None:
        defult_plugins_loc = self.plugins.index('DefaultPlugins')
        self.plugins[defult_plugins_loc:defult_plugins_loc+1] = self.DEFAULT_PLUGINS


@dataclass
class StreamConfig(ConfigBase):
    plugin: str
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildConfig(ConfigBase):
    asset_dir: str = 'assets/'
    export_dir: str = '.built_assets/'
    ignore_patterns: list[str] = field(default_factory=lambda:['*blend1', '*.blend2'])
    show_all_jobs: bool = False
    jobs: int = 0
    streams: list[StreamConfig] = field(default_factory=list)


@dataclass
class RunConfig(ConfigBase):
    main_file: str = 'main.py'
    extra_args: str = ''
    auto_build: bool = True


@dataclass
class DistConfig(ConfigBase):
    build_installers: bool = True


@dataclass
class PythonConfig(ConfigBase):
    path: str = ''


@dataclass
class InternalConfig(ConfigBase):
    projectdir: str = ''


@dataclass
class Config(ConfigBase):
    PROJECT_CONFIG_NAMES: ClassVar[list[str]] = [
        'pyproject.toml',
        '.pman',
        '.pman.user',
    ]

    general: GeneralConfig = field(default_factory=GeneralConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    run: RunConfig = field(default_factory=RunConfig)
    dist: DistConfig = field(default_factory=DistConfig)
    python: PythonConfig = field(default_factory=PythonConfig)
    internal: InternalConfig = field(default_factory=InternalConfig)
    plugins: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, startdir: str) -> 'Config':
        try:
            if startdir is None:
                startdir = os.getcwd()
        except FileNotFoundError as exc:
            # The project folder was deleted on us
            raise NoConfigError("Could not find config file") from exc

        dirs = os.path.abspath(startdir).split(os.sep)
        cfgpaths = None

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
                break

            dirs.pop()

        if cfgpaths:
            confs = []
            for confpath in cfgpaths:
                with (open(confpath, 'rb')) as conffile:
                    conf = toml.load(conffile)
                    if 'tool' in conf and 'pman' in conf['tool']:
                        conf = conf['tool']['pman']
                    confs.append(conf)

            confdata = functools.reduce(
                _merge_dict,
                [
                    {},
                    *confs,
                    {
                        'internal': {
                            'projectdir': os.path.dirname(cfgpaths[0]),
                        },
                    },
                ]
            )
            confobj = dataclass_from_dict(cls, confdata)
            plist = plugins.get_plugins(filter_names=confobj.general.plugins)
            for pluginobj in plist:
                if hasattr(pluginobj, 'Config') and hasattr(pluginobj, 'CONFIG_KEY'):
                    configkey = pluginobj.CONFIG_KEY
                    configobj = pluginobj.Config
                    plugconf = dataclass_from_dict(
                        configobj,
                        confdata.get(configkey, {})
                    )
                    setattr(confobj, configkey, plugconf)
                    confobj.plugins[configkey] = plugconf
            return confobj

        # No config found
        raise NoConfigError("Could not find config file")
