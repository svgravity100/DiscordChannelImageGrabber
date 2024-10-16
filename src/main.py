from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox
from PyQt6.QtCore import QThread
from PyQt6.QtGui import QPalette, QColor
from gui import Ui_Dialog
from scripts import GetImage
import sys


class Worker(QThread):

    def __init__(self,):
        super().__init__()
        self.logic = GetImage()

    def run(self):
        self.logic.start()


class MyDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.file_name = None
        self.setupUi(self)
        self.init_UI()
        self.pushButton.clicked.connect(self.first_button_action)
        self.pushButton_2.clicked.connect(self.open_folder_explorer)
        self.worker = Worker()
        self.pushButton.setEnabled(False)
        self.lineEdit.textChanged.connect(self.enable_button)
        self.lineEdit_2.textChanged.connect(self.enable_button)

    def init_UI(self):
        app.setStyle("windowsvista")
        self.progressBar.hide()
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase,
                         QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText,
                         QColor(255, 255, 255))
        app.setPalette(palette)

    def first_button_action(self):
        self.worker.logic.token = self.lineEdit.text()
        self.worker.logic.channel_id = self.lineEdit_2.text()
        self.worker.logic.max_value.connect(self.progressBar.setMaximum)
        self.worker.logic.progress_signal.connect(self.update_progress)
        self.worker.started.connect(self.start_parsing)
        self.worker.finished.connect(self.on_finished)
        self.worker.logic.error.connect(self.show_error_message)
        self.worker.start()

    def open_folder_explorer(self):
        self.folder_name = QFileDialog.getExistingDirectory(
            self, "Open Folder", "", QFileDialog.Option.ShowDirsOnly)
        GetImage.output_folder = self.folder_name

    def enable_button(self):
        if not self.lineEdit.text().strip() and not self.lineEdit.text().strip():
            self.pushButton.setEnabled(False)
        else:
            self.pushButton.setEnabled(True)

    def start_parsing(self):
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        self.lineEdit.setEnabled(False)
        self.lineEdit_2.setEnabled(False)
        self.progressBar.show()

    def on_finished(self):
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.lineEdit.setEnabled(True)
        self.lineEdit_2.setEnabled(True)
        self.progressBar.hide()
        self.progressBar.reset()

    def update_progress(self, value):
        self.progressBar.setValue(value + 1)

    def show_error_message(self, error):
        self.worker.exit(returnCode=0)
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setWindowTitle("Warning")
        dlg.setText(error)
        button = dlg.exec()
        self.worker = Worker()

        if button == QMessageBox.StandardButton.Ok:
            print("OK!")
        self.on_finished()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec())
