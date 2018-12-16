from setuptools import setup

setup(
    name='newgame',
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pylint',
        'pytest-pylint',
    ],
)
