import os

import pytest
import pman

#pylint:disable=redefined-outer-name


@pytest.fixture
def projectdir(tmpdir):
    pman.create_project(tmpdir.strpath)
    return tmpdir.strpath


def test_conf(tmpdir):
    os.chdir(tmpdir.strpath)
    open('.pman', 'w').close()
    conf = pman.get_config()
    pman.write_config(conf)


def test_create_project(tmpdir):
    pman.create_project(tmpdir.strpath)


def test_build(projectdir):
    os.chdir(projectdir)
    pman.build()


# Requires Panda3D to be setup
#def test_run(projectdir):
#    os.chdir(projectdir)
#    pman.run()
