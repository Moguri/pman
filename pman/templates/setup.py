from setuptools import setup

import pman.build_apps

CONFIG = pman.get_config()

APP_NAME = CONFIG['general']['name']

setup(
    name=APP_NAME,
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pylint~=2.6.0',
        'pytest-pylint',
    ],
    cmdclass={
        'build_apps': pman.build_apps.BuildApps,
    },
    options={
        'build_apps': {
            'include_patterns': [
                CONFIG['build']['export_dir']+'/**',
                'settings.prc',
            ],
            'rename_paths': {
                CONFIG['build']['export_dir']: 'assets/',
            },
            'gui_apps': {
                APP_NAME: CONFIG['run']['main_file'],
            },
            'plugins': [
                'pandagl',
                'p3openal_audio',
            ],
        },
    }
)
