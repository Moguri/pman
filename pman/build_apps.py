from . import core

try:
    from direct.dist.commands import build_apps

    class BuildApps(build_apps):
        def run(self):
            # Run pman build first
            core.build()

            # Run regular build_apps
            build_apps.run(self)
except ImportError:
    class BuildApps(object):
        def __init__(self):
            pass

        def run(self):
            raise NotImplementedError(
                "Setuptools distribution not supported by this version of Panda3D"
            )
