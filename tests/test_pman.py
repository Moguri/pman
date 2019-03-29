import os

import pytest
import pman

#pylint:disable=redefined-outer-name
#pylint:disable=unused-argument


@pytest.fixture
def projectdir(tmpdir):
    pman.create_project(tmpdir.strpath)
    os.chdir(tmpdir.strpath)


def test_conf(tmpdir):
    open('.pman', 'w').close()
    conf = pman.get_config()
    pman.write_config(conf)


def test_create_project(projectdir):
    # projectdir already creates a project
    pass


def test_build(projectdir):
    pman.build()


def test_create_renderer(projectdir):
    conf = pman.get_config()
    conf['general']['renderer'] = 'none'
    pman.build()
    pman.create_renderer(None, conf)


def test_venv_detect(projectdir):
    user_confg = pman.get_user_config()
    assert user_confg['python']['in_venv']


PRINT_VENV_SCRIPT = """
import os
import pman
with open('{}', 'w') as f:
    f.write(str(pman.in_venv()))
"""
def test_run_script(projectdir):
    conf = pman.get_config()
    scriptloc = 'script.py'
    outputloc = 'output'
    with open(scriptloc, 'w') as scriptfile:
        scriptfile.write(PRINT_VENV_SCRIPT.format(outputloc))
    pman.run_script(
        conf,
        [scriptloc],
        cwd=conf['internal']['projectdir']
    )

    assert os.path.exists(outputloc)
    with open(outputloc) as outputfile:
        assert outputfile.read() == 'True'


# def test_run(projectdir):
#     pman.run()
