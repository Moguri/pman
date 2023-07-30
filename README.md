![Build Status](https://github.com/Moguri/panda3d-pman/workflows/Pipeline/badge.svg)
[![](https://img.shields.io/github/license/Moguri/pman.svg)](https://choosealicense.com/licenses/mit/)


# Panda3D Manager
pman is a Python package to help bootstrap and manage [Panda3D](https://github.com/panda3d/panda3d) applications.

## Features

* Project quick-start
* Automatic asset conversion
* Automatically adds export directory to the model path
* Convenient CLI for running and testing applications
* Plugin system for expanding functionality

## Installation

Use [pip](https://github.com/panda3d/panda3d) to install the `panda3d-pman` package:

```bash
pip install panda3d-pman
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

* update - re-run project creation logic on the project directory
* help - display usage information
* build - convert all files in the assets directory and place them in the export directory
* run - run the application by calling `python` with the main file
* test - run tests (shortcut for `python setup.py test`)
* dist - create distributable forms of Panda3D applications (requires Panda3D 1.10+)
* clean - remove built files

## Configuration

`pman` will look for any of the following files in the project root:
* pyproject.toml
* .pman
* .pman.user

This configuration uses [TOML](https://github.com/toml-lang/toml) for markup.
The `.pman` or `pyproject.toml` configuration file is project-wide and should be checked in under version control.

Another, per-user configuration file also exists at the project root as `.pman.user`.
This configuration file stores user settings and should *not* be checked into version control. 

Settings in `.pman.user` take precedence over settings in `.pman` and both take precedence over `pyproject.toml`.
If a setting is not defined in a config file, a default value will be used.

When storing settings in `pyproject.toml`, section names should be pre-pended with `tool.pman.`.
For example, `general` options would be under `tool.pman.general`.

### General Options
Section name: `general`

|option|default|description|
|---|---|---|
|name|`"Game"`|The project name. For now this is only used for naming the built application in the default `setup.py`.|
|plugins|`["DefaultPlugins"]`|A list of plugins to load and use. `"DefaultPlugins"` is expanded to the current default plugins, which makes it easier to enable additional plugins.|

### Build Options
Section name: `build`

|option|default|description|
|---|---|---|
|asset_dir|`"assets/"`|The directory to look for assets to convert.|
|export_dir|`".built_assets/"`|The directory to store built assets.|
|ignore_patterns|`[]`|A case-insensitive list of patterns. Files matching any of these patterns will not be ignored during the build step. Pattern matching is done using [the fnmatch module](https://docs.python.org/3/library/fnmatch.html)

### Run Options
Section name: `run`

|option|default|description|
|---|---|---|
|main_file|`"main.py"`|The entry-point to the application.|
|extra_args|`""`|A string of extra arugments that are append to the invocation of `main_file`.|
|auto_build|`true`|If `true`, automatically run builds as part of running the application (via `pman.shim.init`). This is disabled in deployed applications.|

### Distribution Options
Section name: `dist`

|option|default|description|
|---|---|---|
|build_installers|`true`|Whether or not to build installers for built applications (i.e., run `bdist_apps`).|

## Plugins

To extend functionality, pman offers a plugin system.
These plugins are found by pman using [entry points](https://packaging.python.org/specifications/entry-points/).

### Default Plugins

By default, pman loads the following plugins:

* native2bam
* blend2bam

When specifying plugins, a special `DefaultPlugins` string is available that expands to pman's current default plugins.
For example, to use `MyAwesomePlugin` in addition to pman's default plugins use:

```toml
[General]
plugins = ['DefaultPlugins', 'MyAwesomePlugin']
```

### Built-in Plugins

Below are plugins that ship with pman and their options.

#### native2bam
Support file formats: `egg`, `egg.pz`, `obj` (and `mtl`), `fbx`, `dae`, `ply`

Loads the file into Panda and saves the result out to BAM. This relies on Panda's builtin file loading capabilities.

##### Options
None

#### blend2bam
Supported file formats: `blend`

Converts Blender files to BAM files via [blend2bam](https://github.com/Moguri/blend2bam).

##### Options
Section name: `blend2bam`

|option|default|description|
|---|---|---|
|material_mode|`"pbr"`|Specify whether to use the default Panda materials ("legacy") or Panda's new PBR material attributes ("pbr"). This is only used by the "gltf" pipeline; the "egg" always uses "legacy".|
|physics_engine|`"builtin"`|The physics engine that collision solids should be built for. To export for Panda's builtin collision system, use "builtin." For Bullet, use "bullet." This is only used by the "gltf" pipeline; the "egg" pipeline always uses "builtin."|
|pipeline|`"gltf"`|The backend that blend2bam uses to convert blend files. Go [here](https://github.com/Moguri/blend2bam#pipelines) for more information.|

## Running Tests

First install the project in editable mode along with `test` extras:

```bash
pip install -e .[test]
```

Then run the test suite with `pytest`:

```bash
pytest
```

## Building Wheels

Install `build`:

```bash
pip install --upgrade build
```

and run:

```bash
python -m build
```
## License

[MIT](https://choosealicense.com/licenses/mit/)
