import pman
import pman.shim

#pylint:disable=unused-argument


def test_create_project(projectdir):
    # projectdir already creates a project
    pass


def test_build(projectdir):
    pman.build()


def test_run_script(projectdir):
    conf = pman.get_config()
    scriptloc = 'script.py'
    with open(scriptloc, 'w') as scriptfile:
        scriptfile.write('import sys; sys.exit(0)')
    pman.run_script(
        conf,
        [scriptloc],
        cwd=conf['internal']['projectdir']
    )


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

def test_shim(projectdir):
    pman.shim.init(None)
