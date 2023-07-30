import os
import tomli as toml

def finalize_distribution_options(dist):
    from ._utils import get_config

    config = get_config()
    assertdir = config['build']['asset_dir']
    exportdir = config['build']['export_dir']
    mainfile = config['run']['main_file']

    pyproject_path = os.path.join(
        config['internal']['projectdir'],
        'pyproject.toml'
    )

    projectname = None

    if os.path.exists(pyproject_path):
        with open(pyproject_path, 'rb') as conffile:
            conf = toml.load(conffile)

            projectname = conf['project']['name']

    cmd = dist.get_command_obj('build_apps')

    # Setup export dir as the new asset dir
    cmd.include_patterns.append(f'{exportdir}/**')
    cmd.rename_paths[exportdir] = assertdir

    # Add an application if there isn't one defined
    if mainfile not in cmd.gui_apps.values() and projectname not in cmd.gui_apps:
        cmd.gui_apps[projectname] = mainfile


finalize_distribution_options.order = 100
