# Лабораторная работа №4

import sys
from ui.my_gui import *

app, application = None, None


class MainWin(QtWidgets.QMainWindow):
    ui = None

    def __init__(self):
        super().__init__()
        self.ui = GuiMainWin()
        self.ui.setupUi(self)
        self.setAnimated(True)
        self.setUpdatesEnabled(True)


def main():
    global app, application
    app = QtWidgets.QApplication([])
    dir_ = QtCore.QDir("Roboto")
    _id = QtGui.QFontDatabase.addApplicationFont("Roboto/Roboto-Regular.ttf")

    application = MainWin()
    application.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
