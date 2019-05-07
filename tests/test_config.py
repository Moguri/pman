import os

import pman
from pman.config import ConfigDict


#pylint:disable=unused-argument

def test_conf_read_write(tmpdir):
    os.chdir(tmpdir.strpath)
    open('.pman', 'w').close()
    conf = pman.get_config()
    pman.write_config(conf)


def test_conf_override(projectdir):
    config_defaults = ConfigDict.CONFIG_DEFAULTS

    # Check default
    config = pman.get_config()
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
    assert config['general']['physics_engine'] == config_defaults['general']['physics_engine']

    # Check that non-overridden project settings are still intact
    assert config['general']['renderer'] == 'basic'
