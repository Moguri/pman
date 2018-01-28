import sys

from direct.showbase.ShowBase import ShowBase
import blenderpanda


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        self.accept('escape', sys.exit)


APP = GameApp()
APP.run()
