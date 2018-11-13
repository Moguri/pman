import sys

from direct.showbase.ShowBase import ShowBase
import pman.shim


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        self.accept('escape', sys.exit)


APP = GameApp()
APP.run()
