import collections
import functools
import os

from . import toml
from .exceptions import NoConfigError


class ConfigDict:
    '''Extend ChainMap to provide a config object with overlays'''

    _CONFIG_DEFAULTS = collections.OrderedDict([
        ('general', collections.OrderedDict([
            ('name', 'Game'),
            ('renderer', 'none'),
        ])),
        ('build', collections.OrderedDict([
            ('asset_dir', 'assets/'),
            ('export_dir', '.built_assets/'),
            ('ignore_patterns', []),
            ('converters', ['native2bam']),
        ])),
        ('run', collections.OrderedDict([
            ('main_file', 'main.py'),
            ('extra_args', ''),
            ('auto_build', True),
            ('auto_save', True),
        ])),
        ('python', collections.OrderedDict([
            ('path', ''),
            ('in_venv', False),
        ])),
        ('blend2bam', collections.OrderedDict([
            ('material_mode', 'legacy'),
            ('physics_engine', 'builtin'),
            ('pipeline', 'gltf'),
            ('overrides', []),
        ])),
    ])

    PROJECT_CONFIG_NAME = '.pman'
    USER_CONFIG_NAME = '{}.user'.format(PROJECT_CONFIG_NAME)

    def __init__(self, project_conf_file, user_conf_file):
        project_conf = toml.load(project_conf_file)
        user_conf = {}
        if os.path.exists(user_conf_file):
            user_conf = toml.load(user_conf_file)
        self.layers = collections.OrderedDict([
            ('default', self._CONFIG_DEFAULTS),
            ('project', project_conf),
            ('user', user_conf),
            ('internal', {
                'internal': {
                    'projectdir': os.path.dirname(project_conf_file),
                },
            }),
        ])

        self._update_conf()


    def __getitem__(self, key):
        def merge_dict(dicta, dictb):
            dicta.update(dictb)
            return dicta
        return functools.reduce(merge_dict, [i.get(key, {}) for i in self.layers.values()])

    def __setitem__(self, key, value):
        self.layers[key] = value

    def __contains__(self, item):
        for layer in self.layers.values():
            if item in layer:
                return True

        return False

    def _update_conf(self):
        '''Handle updating old configs or fields that change on load'''

        confs = [
            self.layers['project'],
            self.layers['user'],
        ]

        for conf in confs:
            if 'general' in conf:
                blend2bam_dict = {}
                if 'material_mode' in conf['general']:
                    blend2bam_dict['material_mode'] = conf['general']['material_mode']
                    del conf['general']['material_mode']
                if 'physics_engine' in conf['general']:
                    blend2bam_dict['physics_engine'] = conf['general']['physics_engine']
                    del conf['general']['physics_engine']
                if blend2bam_dict:
                    conf['blend2bam'] = blend2bam_dict
                    self.write()

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

    def write(self):
        project_conf_name = os.path.join(self['internal']['projectdir'], self.PROJECT_CONFIG_NAME)
        with open(project_conf_name, 'w') as project_conf_file:
            toml.dump(self.layers['project'], project_conf_file)

        user_conf_name = os.path.join(self['internal']['projectdir'], self.USER_CONFIG_NAME)
        with open(user_conf_name, 'w') as user_conf_file:
            toml.dump(self.layers['user'], user_conf_file)
