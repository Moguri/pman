import os

import pytest

import pman

#pylint:disable=redefined-outer-name
#pylint:disable=unused-argument

@pytest.fixture
def projectdir(tmpdir):
    pman.create_project(tmpdir.strpath)
    os.chdir(tmpdir.strpath)

@pytest.fixture
def projectconf(projectdir):
    with open('.pman', 'w') as f:
        yield f

@pytest.fixture
def userconf(projectdir):
    with open('.pman.user', 'w') as f:
        yield f
