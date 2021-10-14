import sys
import asyncio, logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from typing import Optional

from ui.my_gui import *
from client import TorrentClient
from torfile import Torrent
import cli

app, application = None, None


class Worker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    tor_client: Optional[TorrentClient] = None

    def __init__(self, tor_path: str, file_path: str):
        super().__init__()
        self.tor_path = tor_path
        self.file_path = file_path

    @pyqtSlot()
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.tor_client = TorrentClient(Torrent(self.tor_path), self.file_path)
        task = loop.create_task(self.tor_client.start())

        self.started.emit()
        try:
            loop.run_until_complete(task)
        except Exception as e:
            logging.info("event loop was cancelled")
        self.finished.emit()


class MainWin(QtWidgets.QMainWindow):
    upd_period = 500  # mseconds

    ui = None
    tor: Optional[TorrentClient] = None
    obj: Optional[Worker] = None
    thread: Optional[QThread] = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = GuiMainWin(self)
        self.ui.setupUi(self)

        self.setAnimated(True)
        self.setUpdatesEnabled(True)

        # setup timer for torrent status update
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.upd_torinfo)

    def start_loading(self, tor_path: str, file_path: str):
        print('Loading files', tor_path, file_path)

        self._init_worker(tor_path, file_path)
        self._init_thread()
        self.thread.start()

    def _init_worker(self, tor_path: str, file_path: str):
        self.obj = Worker(tor_path, file_path)
        self.obj.started.connect(self.on_tor_start)
        self.obj.finished.connect(self.on_tor_done)

    def _init_thread(self):
        self.thread = QThread()
        self.obj.moveToThread(self.thread)
        self.thread.started.connect(self.obj.run)

    @pyqtSlot()
    def on_tor_start(self):
        self.tor = self.obj.tor_client
        self.timer.start(self.upd_period)

    @pyqtSlot()
    def upd_torinfo(self):
        self.ui.upd_torrent(self.tor)

    @pyqtSlot()
    def on_tor_done(self):
        print('loading is over')
        self.timer.stop()


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
