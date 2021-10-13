from .gui import *

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QGuiApplication
from math import *
from time import *
from matplotlib import pyplot


class GuiMainWin(Ui_Window):
    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
