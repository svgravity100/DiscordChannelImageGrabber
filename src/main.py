import sys
import os

os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication

import generated.resources_rc  # регистрирует QML-файлы в Qt Resource System
from backend import Backend


def main() -> None:
    # QApplication (не QGuiApplication) — нужен для QSystemTrayIcon и QFileDialog
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    backend = Backend()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)

    # QML загружается из бинарных ресурсов, а не с диска
    engine.load(QUrl("qrc:/qml/main.qml"))

    if not engine.rootObjects():
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
