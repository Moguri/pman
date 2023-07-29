import sys

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman.shim


panda3d.core.load_prc_file_data(
    '',
    'window-title Panda3D Game\n'
)


class GameApp(ShowBase):
    def __init__(self):
        pman.shim.init(self)
        ShowBase.__init__(self)
        self.accept('escape', sys.exit)


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
