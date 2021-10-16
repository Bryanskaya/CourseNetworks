from .gui import *
from client import TorrentClient

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QGuiApplication
from PyQt5.QtWidgets import QFileDialog
from math import *
from time import *
from matplotlib import pyplot


class GuiMainWin(QtWidgets.QWidget, Ui_Window):
    def __init__(self, parent:QtWidgets.QMainWindow):
        super(GuiMainWin, self).__init__(parent)

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.set_binds()
        self._set_action_start()

    def set_binds(self):
        self.openTorBtn.clicked.connect(self.open_tor)
        self.openLocBtn.clicked.connect(self.open_loc)
        self.startBtn.clicked.connect(self._start_load)
        self.stopBtn.clicked.connect(self._stop_load)

    def open_tor(self):
        init_path = 'c:\\'
        if self.torLine.text():
            init_path = self.torLine.text()
            path_parts = init_path.split('/')
            init_path = init_path[:-len(path_parts[-1])]

        fname = QFileDialog.getOpenFileName(self, 'Выберите файл', init_path, "Torrent files (*.torrent)")
        if fname and fname[0]:
            self.torLine.setText(fname[0])

    def open_loc(self):
        init_path = 'c:\\'
        if self.locLine.text():
            init_path = self.locLine.text()

        fname = QFileDialog.getExistingDirectory(self, 'Выберите место загрузки', init_path)
        if fname:
            self.locLine.setText(fname)

    def upd_torrent(self, tor: TorrentClient):
        self.totalSizeL.setText('{:0,.1f} КБ'.format(tor.total_size / 1024).replace(',', ' '))
        self.loadSizeL.setText('{:0,.1f} КБ'.format(tor.loaded_bytes / 1024).replace(',', ' '))
        self.peerNL.setText('{}'.format(tor.active_peer_n))

    def _start_load(self):
        tor_path = self.torLine.text()
        file_path = self.locLine.text()

        if tor_path and file_path:
            self._set_action_stop()
            self.parent().start_loading(tor_path, file_path)
        else:
            self._show_cantload()

    def _stop_load(self):
        pass

    def _set_action_stop(self):
        self.stopBtn.show()
        self.startBtn.hide()

    def _set_action_start(self):
        self.stopBtn.hide()
        self.startBtn.show()

    def _show_cantload(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(msg.Critical)
        msg.setText("Невозможно начать загрузку")
        msg.setInformativeText('Укажите путь к torrent-файлу и директорию загрузеи')
        msg.setWindowTitle("Ошибка")
        msg.exec_()
