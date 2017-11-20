from setuptools import setup


setup(
    name='panda3d_pman',
    version='0.1',
    description='A Python package to help bootstrap and manage Panda3D applications',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='panda3d gamedev',
    url='https://github.com/Moguri/pman',
    author='Mitchell Stokes',
    license='MIT',
    packages=['pman'],
    setup_requires=['pytest-runner', 'pytest-pylint'],
    tests_require=['pytest', 'pylint'],
)
