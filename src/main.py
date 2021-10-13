import sys
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from ui.my_gui import *
import cli

app, application = None, None


class Worker(QObject):
    finished = pyqtSignal()

    def __init__(self, tor_path: str, file_path: str):
        super().__init__()
        self.tor_path = tor_path
        self.file_path = file_path

    @pyqtSlot()
    def run(self):
        cli.run_loading(self.tor_path, self.file_path)
        self.finished.emit()


class MainWin(QtWidgets.QMainWindow):
    ui = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = GuiMainWin(self)
        self.ui.setupUi(self)

        self.setAnimated(True)
        self.setUpdatesEnabled(True)

    def start_loading(self, tor_path: str, file_path: str):
        print('Loading files', tor_path, file_path)

        self.obj = Worker(tor_path, file_path)
        self.thread = QThread()
        # self.obj.intReady.connect(self.onIntReady)
        self.obj.moveToThread(self.thread)
        # self.obj.finished.connect(self.thread.quit)
        self.thread.started.connect(self.obj.run)
        self.thread.start()


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
