import argparse


import pman


def create(args):
    pman.create_project(args.dirname)


def build(_):
    pman.build()


def run(_):
    pman.run()


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


    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
