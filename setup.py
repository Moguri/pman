from setuptools import setup


setup(
    name='pman',
    setup_requires=['pytest-runner', 'pytest-pylint'],
    tests_require=['pytest', 'pylint'],
)
