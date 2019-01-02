from __future__ import print_function

import argparse
import subprocess


import pman


def create(args):
    pman.create_project(args.dirname)


def build(_):
    pman.build()


def run(_):
    pman.run()


def test(_):
    config = pman.get_config()
    args = [
        pman.get_python_program(),
        'setup.py',
        'test',
    ]
    subprocess.call(args, cwd=config['internal']['projectdir'])


def dist(args):
    pman.get_python_program()

    try:
        import direct.dist.commands #pylint:disable=unused-import,unused-variable
    except ImportError:
        print('Setuptools-based distribution is not supported by this version of Panda3D')
        return

    platforms = args.platforms
    if platforms is not None:
        platforms = list(platforms)
    pman.dist(build_installers=not args.skip_installers, platforms=platforms)


def main():
    parser = argparse.ArgumentParser(
        description='Tool for building and managing Panda3D applications'
    )

    subparsers = parser.add_subparsers(
        title='commands',
        required=True,
    )

    create_parser = subparsers.add_parser(
        'create',
        help='Create a new project',
    )
    create_parser.add_argument(
        'dirname',
        action='store',
        nargs='?',
        default='.',
        help='Directory to create the project in (will be created if it does not exist)',
    )
    create_parser.set_defaults(func=create)

    build_parser = subparsers.add_parser(
        'build',
        help='Build project',
    )
    build_parser.set_defaults(func=build)

    run_parser = subparsers.add_parser(
        'run',
        help='Run project',
    )
    run_parser.set_defaults(func=run)

    test_parser = subparsers.add_parser(
        'test',
        help='Run tests',
    )
    test_parser.set_defaults(func=test)

    dist_parser = subparsers.add_parser(
        'dist',
        help='Create binary distributions and installers'
    )
    dist_parser.add_argument(
        '--skip-installers',
        action='store_true',
        help='Do not build installers',
    )
    dist_parser.add_argument(
        '-p', '--platforms',
        action='store',
        nargs='+',
        help='Override list of platforms to build for',
    )
    dist_parser.set_defaults(func=dist)


    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
