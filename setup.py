from setuptools import setup


__version__ = ''
#pylint: disable=exec-used
exec(open('pman/version.py').read())


setup(
    name='panda3d-pman',
    version=__version__,
    keywords='panda3d gamedev',
    packages=['pman', 'pman.templates'],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'panda3d',
        'pytest',
        'pylint==2.4.*',
        'pytest-pylint',
    ],
    install_requires=[
        'panda3d-blend2bam >=0.5.1',
    ],
    entry_points={
        'console_scripts': [
            'pman=pman.cli:main',
            'native2bam=pman.native2bam:main',
        ],
        'pman.converters': [
            'blend2bam = pman.hooks:converter_blend_bam',
            'native2bam = pman.hooks:converter_native_bam',
        ],
        'pman.renderers': [
            'basic = pman.basicrenderer:BasicRenderer',
            'none = pman.nullrenderer:NullRenderer',
        ],
        'pman.creation_extras': [
            'git = pman.hooks:create_git',
            'blender = pman.hooks:create_blender',
        ],
    },
)
