from setuptools import setup


def readme():
    with open('README.md') as readme_file:
        return readme_file.read()


setup(
    name='panda3d-pman',
    version='0.4',
    description='A Python package to help bootstrap and manage Panda3D applications',
    long_description=readme(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='panda3d gamedev',
    url='https://github.com/Moguri/pman',
    author='Mitchell Stokes',
    license='MIT',
    packages=['pman', 'pman.templates'],
    include_package_data=True,
    install_requires=[
        'panda3d-blend2bam >=0.4',
    ],
    setup_requires=['pytest-runner'],
    tests_require=[
        'panda3d',
        'pytest',
        'pylint==2.2.*',
        'pytest-pylint',
    ],
    entry_points={
        'console_scripts': [
            'pman=pman.cli:main',
        ],
        'pman.converters': [
            'blend2bam = pman.hooks:converter_blend_bam',
        ],
        'pman.renderers': [
            'basic = pman.basicrenderer:BasicRenderer',
            'none = pman.nullrenderer:NullRenderer',
        ],
    },
)
