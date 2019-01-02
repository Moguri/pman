import os

import pytest
import pman

#pylint:disable=redefined-outer-name
#pylint:disable=unused-argument


@pytest.fixture
def projectdir(tmpdir):
    pman.create_project(tmpdir.strpath)
    os.chdir(tmpdir.strpath)

def test_load_module():
    pman.load_module('pman.hooks')


def test_conf(tmpdir):
    open('.pman', 'w').close()
    conf = pman.get_config()
    pman.write_config(conf)


def test_create_project(projectdir):
    # projectdir already creates a project
    pass


def test_build(projectdir):
    pman.build()

# def test_run(projectdir):
#     pman.run()
