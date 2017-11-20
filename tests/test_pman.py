import os

import pman


def test_get_conf(tmpdir):
    os.chdir(tmpdir.strpath)
    open('.pman', 'w').close()
    _ = pman.get_config()


def test_create_project(tmpdir):
    pman.create_project(tmpdir.strpath)
