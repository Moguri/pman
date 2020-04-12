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
