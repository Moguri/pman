import os

import pman


#pylint:disable=unused-argument

def test_conf_read(tmpdir):
    os.chdir(tmpdir.strpath)
    open('.pman', 'w').close()
    pman.get_config()

def test_load_pyproject(tmpdir):
    os.chdir(tmpdir.strpath)
    with open('pyproject.toml', 'w') as pyproject:
        pyproject.write('[metadata]\n')
        pyproject.write('name = "foo"\n')
        pyproject.write('[tool.pman.general]\n')
        pyproject.write('verbose = true\n')
        pyproject.write('[tool.pman.build]\n')
        pyproject.write('asset_dir = "foobar"\n')

    conf = pman.get_config()

    assert conf['general']['verbose']

def test_prefer_pman_over_pyproject(tmpdir):
    os.chdir(tmpdir.strpath)

    with open('pyproject.toml', 'w') as pyproject:
        pyproject.write('[tool.pman.general]\n')
        pyproject.write('name = "pyproject"\n')

    with open('.pman', 'w') as pmanconf:
        pmanconf.write('[general]\n')
        pmanconf.write('name = "pmanconf"\n')

    conf = pman.get_config()
    assert conf['general']['name'] == 'pmanconf'


def test_conf_contains(projectdir):
    config = pman.get_config()

    assert 'general' in config
    assert 'foo' not in config


def test_conf_override(projectdir):
    with open('.pman', 'a') as conffile:
        conffile.write('[general]\n')
        conffile.write('name = "projectname"\n')
        conffile.write('[build]\n')
        conffile.write('export_dir = "assets"\n')

    with open('.pman.user', 'a') as conffile:
        conffile.write('[general]\n')
        conffile.write('name = "username"\n')

    # Check default
    config = pman.get_config()
    assert config['run']['main_file'] == 'main.py'
    assert not config['general']['verbose']

    # Check that project overrides default
    assert config['build']['export_dir'] == 'assets'

    # Check that user overrides default
    assert config['general']['name'] == 'username'


def test_conf_missing(projectdir):
    config = pman.get_config()
    assert config['python']
    assert config['blend2bam']
