[![Build Status](https://travis-ci.org/Moguri/pman.svg?branch=master)](https://travis-ci.org/Moguri/pman)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/panda3d-pman.svg)
[![Panda3D Versions](https://img.shields.io/badge/panda3d-1.9%2C%201.10-blue.svg)](http://www.panda3d.org/)

# Panda3D Manager
pman is a Python package to help bootstrap and manage [Panda3D](https://github.com/panda3d/panda3d) applications.

## Features

* Project quick-start
* Automatic asset conversion
* Automatically adds export directory to the model path
* Convenient CLI for running and testing applications

## Installation

Use [pip](https://github.com/panda3d/panda3d) to install the panda3d_pman package:

```bash
pip install panda3d_pman
```

## Usage

Quick start a project with `pman create`.
If you already have a directory for your project:

```bash
cd my_awesome_project
pman create .
```

`pman` can also create the directory for you:

```bash
pman create my_awesome_project
```

In addition to the `create` command, `pman` has the following commands:

* help - display usage information
* build - convert all files in the assets directory and place them in the export directory
* run - run the application by calling `python` with the main file
* test - run tests (shortcut for `python setup.py test`)

## Configuration

Primary configuration for `pman` is located in a `.pman` file located at the project root.
This configuration uses [TOML](https://github.com/toml-lang/toml) for markup.
The `.pman` configuration file is project-wide and should be checked in under version control.

Another, per-user configuration file also exists at the project root as `.pman.user`.
This configuration file stores user settings and should *not* be checked into version control.

## License

[MIT](https://choosealicense.com/licenses/mit/)
