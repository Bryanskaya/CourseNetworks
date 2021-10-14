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
    finished = pyqtSignal()

    def __init__(self, tor_path: str, file_path: str):
        super().__init__()
        self.tor_path = tor_path
        self.file_path = file_path
        self.tor_client = None

    @pyqtSlot()
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.tor_client = TorrentClient(Torrent(self.tor_path), self.file_path)
        task = loop.create_task(self.tor_client.start())

        try:
            loop.run_until_complete(task)
        except Exception as e:
            logging.info("event loop was cancelled")

        self.finished.emit()


class MainWin(QtWidgets.QMainWindow):
    ui = None
    # worker: Optional[Worker] = None
    thread: Optional[QThread] = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = GuiMainWin(self)
        self.ui.setupUi(self)

        self.setAnimated(True)
        self.setUpdatesEnabled(True)

    def start_loading(self, tor_path: str, file_path: str):
        print('Loading files', tor_path, file_path)

        self._init_thread(tor_path, file_path)
        self.thread.start()

    def _init_thread(self, tor_path: str, file_path: str):
        self.obj = Worker(tor_path, file_path)
        self.thread = QThread()
        # self.obj.intReady.connect(self.onIntReady)
        self.obj.moveToThread(self.thread)
        self.obj.finished.connect(self.on_tor_done)
        self.thread.started.connect(self.obj.run)

    @pyqtSlot()
    def on_tor_done(self):
        print('hello')


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
