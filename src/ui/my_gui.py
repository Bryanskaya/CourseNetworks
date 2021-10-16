from .gui import *
from client import TorrentClient

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QGuiApplication, QBrush, QColor, QPen
from PyQt5.QtWidgets import QFileDialog, QGraphicsScene
from math import *
from time import *
from matplotlib import pyplot
import bitstring


class GuiMainWin(QtWidgets.QWidget, Ui_Window):
    def __init__(self, parent:QtWidgets.QMainWindow):
        super(GuiMainWin, self).__init__(parent)
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QColor(246, 239, 219))

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.set_binds()
        self.set_action_start()
        self.loadBar.setScene(self.scene)
        self.loadBar.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.loadBar.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.loadBar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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
        self.scene.clear()
        self.scene.setSceneRect(0, 0, len(tor.loaded_map)+1, 1)
        self.loadBar.fitInView(self.scene.sceneRect(), Qt.IgnoreAspectRatio)

        self.totalSizeL.setText('{:0,.1f} КБ'.format(tor.total_size / 1024).replace(',', ' '))
        self.loadSizeL.setText('{:0,.1f} КБ'.format(tor.loaded_bytes / 1024).replace(',', ' '))
        self.peerNL.setText('{}'.format(tor.active_peer_n))
        self._show_map(tor.ongoing_map, QPen(QColor(253, 216, 91)))
        self._show_map(tor.loaded_map, QPen(QColor(105, 187, 112)))

    def set_action_stop(self):
        self.stopBtn.show()
        self.startBtn.hide()

    def set_action_start(self):
        self.stopBtn.hide()
        self.startBtn.show()

    def _start_load(self):
        tor_path = self.torLine.text()
        file_path = self.locLine.text()

        if tor_path and file_path:
            self.set_action_stop()
            self.parent().start_loading(tor_path, file_path)
        else:
            self._show_cantload()

    def _stop_load(self):
        self.parent().stop_loading()
        self.stopBtn.setDisabled(True)

    def _show_cantload(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(msg.Critical)
        msg.setText("Невозможно начать загрузку")
        msg.setInformativeText('Укажите путь к torrent-файлу и директорию загрузеи')
        msg.setWindowTitle("Ошибка")
        msg.exec_()

    def _show_map(self, m: bitstring.BitArray, pen: QPen):
        x = 0
        for elem in m:
            if elem:
                self.scene.addRect(x, 0, 1, 1, pen)

            x += 1
