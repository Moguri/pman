import os

import pman

#pylint:disable=unused-argument


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


EXTRA_ARGS_MAIN = """
import sys
with open('tmp', 'w') as f:
    f.write(repr(sys.argv[1:]))
"""
def test_run_args(projectdir):
    with open('main.py', 'w') as main_file:
        main_file.write(EXTRA_ARGS_MAIN)

    config = pman.get_config()
    config['run']['extra_args'] = "--test 'hello world'"
    config.write()

    pman.run()

    with open('tmp', 'r') as tmpfile:
        assert tmpfile.read() == "['--test', 'hello world']"
