import os

import pman


#pylint:disable=unused-argument

def test_conf_read_write(tmpdir):
    os.chdir(tmpdir.strpath)
    open('.pman', 'w').close()
    conf = pman.get_config()
    pman.write_config(conf)


def test_conf_contains(projectdir):
    config = pman.get_config()

    assert 'general' in config
    assert 'foo' not in config


def test_conf_override(projectdir):
    # Check default
    config = pman.get_config()
    config_defaults = config.layers['default']
    assert config['general']['name'] == config_defaults['general']['name']

    # Check that project overrides default
    project_layer = config.layers['project']
    project_layer['general'] = {
        'name': 'projectname',
        'renderer': 'basic',
    }
    assert config['general']['name'] == 'projectname'

    # Check that user overrides default
    user_layer = config.layers['user']
    user_layer['general'] = {
        'name': 'username',
    }
    assert config['general']['name'] == 'username'

    # Check that non-overridden default settings are still intact
    assert config['build']['asset_dir'] == config_defaults['build']['asset_dir']

    # Check that non-overridden project settings are still intact
    assert config['general']['renderer'] == 'basic'

def test_conversion(projectdir):
    config = pman.get_config()
    config.layers['project']['general'] = {
        'material_mode': 'pbr',
    }
    config.write()

    config = pman.get_config()
    assert config['blend2bam']['material_mode'] == 'pbr'

def test_conf_missing(projectdir):
    config = pman.get_config()
    assert config['python']
    assert config['blender']


PROJECT_CONF_DATA = '''
[run]
auto_build = false

[general]
name = "GameName"
'''.strip()

EXPECTED_CONF_DATA = '''
[run]
auto_build = false
main_file = "foo.py"

[general]
name = "GameName"
'''.strip()
def test_conf_order(projectdir):
    confloc = pman.ConfigDict.PROJECT_CONFIG_NAME
    with open(confloc, 'w') as conffile:
        conffile.write(PROJECT_CONF_DATA)

    config = pman.get_config()
    config.layers['project']['run']['main_file'] = 'foo.py'
    config.write()
    with open(confloc) as conffile:
        readdata = conffile.read().strip()

    assert readdata == EXPECTED_CONF_DATA
