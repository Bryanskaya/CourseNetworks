from .gui import *

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QGuiApplication
from PyQt5.QtWidgets import QFileDialog
from math import *
from time import *
from matplotlib import pyplot


class GuiMainWin(Ui_Window, QtWidgets.QWidget):
    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.set_binds()

    def set_binds(self):
        self.openTorBtn.clicked.connect(self.open_tor)

    def open_tor(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            'c:\\', "Torrent files (*.torrent)")
        print(fname[0])
        self.torLine.setText(fname[0])
