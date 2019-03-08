import os
import sys

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman.shim


if hasattr(sys, 'frozen'):
    APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    APP_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
APP_ROOT_DIR = panda3d.core.Filename.from_os_specific(APP_ROOT_DIR)

panda3d.core.load_prc_file(panda3d.core.Filename(APP_ROOT_DIR, 'settings.prc'))


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        self.accept('escape', sys.exit)


APP = GameApp()
APP.run()
