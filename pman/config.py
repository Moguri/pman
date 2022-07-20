import functools
import os
import tomli as toml

from .exceptions import NoConfigError


class ConfigDict:
    '''Extend ChainMap to provide a config object with overlays'''

    _CONFIG_DEFAULTS = {
        'general': {
            'name': 'Game',
            'verbose': False,
        },
        'build': {
            'asset_dir': 'assets/',
            'export_dir': '.built_assets/',
            'ignore_patterns': ['*.blend1', '*.blend2'],
            'converters': ['native2bam', 'blend2bam'],
        },
        'run': {
            'main_file': 'main.py',
            'extra_args': '',
            'auto_build': True,
            'auto_save': True,
        },
        'python': {
            'path': '',
        },
        'blend2bam': {
            'blender_dir': '',
            'material_mode': 'pbr',
            'physics_engine': 'builtin',
            'pipeline': 'gltf',
            'animations': 'embed',
            'overrides': [],
        },
    }

    PROJECT_CONFIG_NAME = '.pman'
    USER_CONFIG_NAME = f'{PROJECT_CONFIG_NAME}.user'

    def __init__(self, project_conf_file, user_conf_file):
        with open(project_conf_file, 'rb') as conffile:
            project_conf = toml.load(conffile)
        user_conf = {}
        if os.path.exists(user_conf_file):
            with open(user_conf_file, 'rb') as conffile:
                user_conf = toml.load(conffile)
        self.layers = {
            'default': self._CONFIG_DEFAULTS,
            'project': project_conf,
            'user': user_conf,
            'internal': {
                'internal': {
                    'projectdir': os.path.dirname(project_conf_file),
                },
            },
        }


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
