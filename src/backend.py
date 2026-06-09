from __future__ import annotations

import os

from PySide6.QtCore import QLocale, QObject, QSettings, QThread, Qt, Property, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QMenu, QSystemTrayIcon

from scripts import GetImage
from strings import STRINGS

_THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg_card":          "#313338",
        "bg_input":         "#1e1f22",
        "bg_input_dis":     "#2b2d31",
        "bg_btn_sec":       "#4e5058",
        "bg_btn_sec_hov":   "#6d6f78",
        "bg_btn_sec_press": "#43444b",
        "bg_dialog":        "#2b2d31",
        "bg_err_icon":      "#3d1517",
        "text_primary":     "#f2f3f5",
        "text_input":       "#dbdee1",
        "text_secondary":   "#b5bac1",
        "text_muted":       "#949ba4",
        "text_label":       "#b5bac1",
        "text_placeholder": "#4e5058",
        "text_btn_sec":     "#dbdee1",
        "separator":        "#3f4147",
        "accent":           "#5865f2",
        "accent_hover":     "#4752c4",
        "accent_pressed":   "#3c45a5",
        "close_hover":      "#ed4245",
        "err_icon":         "#ed4245",
        "border_input":     "#1e1f22",
        "overlay":          "#b2000000",
    },
    "light": {
        "bg_card":          "#f2f3f5",
        "bg_input":         "#ffffff",
        "bg_input_dis":     "#e3e5e8",
        "bg_btn_sec":       "#e3e5e8",
        "bg_btn_sec_hov":   "#d4d7dc",
        "bg_btn_sec_press": "#c7ccd4",
        "bg_dialog":        "#ffffff",
        "bg_err_icon":      "#fde8e8",
        "text_primary":     "#060607",
        "text_input":       "#2e3338",
        "text_secondary":   "#4e5058",
        "text_muted":       "#6d6f78",
        "text_label":       "#4e5058",
        "text_placeholder": "#8e9297",
        "text_btn_sec":     "#4e5058",
        "separator":        "#e3e5e8",
        "accent":           "#5865f2",
        "accent_hover":     "#4752c4",
        "accent_pressed":   "#3c45a5",
        "close_hover":      "#ed4245",
        "err_icon":         "#ed4245",
        "border_input":     "#d4d7dc",
        "overlay":          "#80000000",
    },
}


class _Worker(QThread):
    def __init__(self) -> None:
        super().__init__()
        self.logic = GetImage()

    def run(self) -> None:
        self.logic.start()


class Backend(QObject):
    stringsChanged     = Signal()
    downloadingChanged = Signal()
    progressChanged    = Signal()
    folderChanged      = Signal()
    themeChanged       = Signal()
    closeRequested     = Signal()  # QML вызывает Qt.quit()
    hideWindow         = Signal()
    showWindow         = Signal()
    errorMessage       = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._downloading: bool = False
        self._progress: int = 0
        self._total: int = 0
        self._folder: str = ""
        self._had_error: bool = False
        self._pending_token: str = ""
        self._settings = QSettings("DiscordImageGrabber", "App")
        self._saved_token: str = self._settings.value("token", "").strip()
        self._lang: str = self._load_lang()
        self._theme: str = self._load_theme()
        self._worker = _Worker()
        self._connect_worker()
        self._setup_tray()

    def _load_lang(self) -> str:
        saved = self._settings.value("lang", "")
        if saved in ("en", "ru"):
            return saved
        system_lang = QLocale.system().name()
        return "ru" if system_lang.startswith("ru") else "en"

    def _load_theme(self) -> str:
        saved = self._settings.value("theme", "")
        if saved in ("dark", "light"):
            return saved
        return self._detect_os_theme()

    def _detect_os_theme(self) -> str:
        try:
            scheme = QApplication.styleHints().colorScheme()
            return "dark" if scheme == Qt.ColorScheme.Dark else "light"
        except Exception:
            return "dark"

    # ── свойства ──────────────────────────────────────────────────────────────

    @Property(str, constant=True)
    def savedToken(self) -> str:
        return self._saved_token

    @Property(str, notify=stringsChanged)
    def lang(self) -> str:
        return self._lang

    @Property(str, notify=themeChanged)
    def theme(self) -> str:
        return self._theme

    @Property("QVariantMap", notify=themeChanged)
    def colors(self) -> dict:
        return _THEMES[self._theme]

    @Property("QVariantMap", notify=stringsChanged)
    def strings(self) -> dict:
        return STRINGS[self._lang]

    @Property(bool, notify=downloadingChanged)
    def downloading(self) -> bool:
        return self._downloading

    @Property(int, notify=progressChanged)
    def progress(self) -> int:
        return self._progress

    @Property(int, notify=progressChanged)
    def total(self) -> int:
        return self._total

    @Property(str, notify=progressChanged)
    def progressText(self) -> str:
        if self._total == 0:
            return STRINGS[self._lang]["collecting"]
        return f"{self._progress} / {self._total}"

    @Property(str, notify=folderChanged)
    def folderDisplay(self) -> str:
        if not self._folder:
            return STRINGS[self._lang]["no_folder"]
        return os.path.basename(self._folder) or self._folder

    # ── слоты, вызываемые из QML ──────────────────────────────────────────────

    @Slot()
    def toggleLanguage(self) -> None:
        self._lang = "ru" if self._lang == "en" else "en"
        self._settings.setValue("lang", self._lang)
        self._update_tray_menu()
        self.stringsChanged.emit()
        self.folderChanged.emit()
        self.progressChanged.emit()

    @Slot()
    def toggleTheme(self) -> None:
        self._theme = "light" if self._theme == "dark" else "dark"
        self._settings.setValue("theme", self._theme)
        self.themeChanged.emit()

    @Slot()
    def chooseFolder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            None,
            STRINGS[self._lang]["choose_save"],
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._folder = folder
            self.folderChanged.emit()

    @Slot(str, str)
    def startDownload(self, token: str, channel_id: str) -> None:
        token = token.strip()
        channel_id = channel_id.strip()
        s = STRINGS[self._lang]

        if not channel_id.isdigit():
            self.errorMessage.emit(s["err_channel_fmt"])
            return

        self._pending_token = token
        self._worker.logic.token = token
        self._worker.logic.channel_id = channel_id
        self._worker.logic.output_folder = self._folder
        self._worker.start()

    @Slot()
    def minimizeToTray(self) -> None:
        self.hideWindow.emit()
        self._tray.show()
        self._tray.showMessage(
            "Discord Image Grabber",
            STRINGS[self._lang]["running_in_bg"],
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    @Slot()
    def requestClose(self) -> None:
        if self._worker.isRunning():
            dlg = QMessageBox()
            dlg.setIcon(QMessageBox.Icon.Question)
            dlg.setWindowTitle(STRINGS[self._lang]["warning"])
            dlg.setText(STRINGS[self._lang]["stop_exit"])
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            dlg.setDefaultButton(QMessageBox.StandardButton.No)
            if dlg.exec() != QMessageBox.StandardButton.Yes:
                return
            self._worker.terminate()
        self._tray.hide()
        self.closeRequested.emit()

    # ── подключение сигналов воркера ──────────────────────────────────────────

    def _connect_worker(self) -> None:
        w = self._worker
        w.logic.max_value.connect(self._on_max_value)
        w.logic.progress_signal.connect(self._on_progress)
        w.logic.error.connect(self._on_error)
        w.started.connect(self._on_started)
        w.finished.connect(self._on_finished)

    def _on_max_value(self, total: int) -> None:
        self._total = total
        self.progressChanged.emit()

    def _on_progress(self, value: int) -> None:
        self._progress = value
        self.progressChanged.emit()

    def _on_started(self) -> None:
        self._downloading = True
        self._progress = 0
        self._total = 0
        self.downloadingChanged.emit()
        self.progressChanged.emit()
        self._tray.setToolTip(STRINGS[self._lang]["tray_dl"])

    def _on_finished(self) -> None:
        had_error = self._had_error
        self._had_error = False

        if not had_error:
            self._settings.setValue("token", self._pending_token)

        self._downloading = False
        self.downloadingChanged.emit()
        self._tray.setToolTip("Discord Image Grabber")
        # поток завершён — безопасно создаём новый воркер
        self._worker = _Worker()
        self._connect_worker()

        if not had_error and not QApplication.activeWindow():
            self._tray.showMessage(
                "Discord Image Grabber",
                STRINGS[self._lang]["done"].format(self._total),
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )

    def _on_error(self, key: str, extra: str) -> None:
        s = STRINGS[self._lang]
        msg = s.get(key, key)
        if extra:
            msg = msg.format(extra)
        self._had_error = True
        self.showWindow.emit()
        self.errorMessage.emit(msg)
        # поток завершится сам, _on_finished вызовется через w.finished

    # ── системный трей ────────────────────────────────────────────────────────

    def _make_tray_icon(self) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor("#5865f2")))
        p.setPen(QColor(0, 0, 0, 0))
        p.drawRoundedRect(0, 0, 32, 32, 8, 8)
        p.end()
        return QIcon(pixmap)

    def _setup_tray(self) -> None:
        self._tray = QSystemTrayIcon(self._make_tray_icon())
        self._tray.setToolTip("Discord Image Grabber")
        self._tray_menu = QMenu()
        self._tray_open = self._tray_menu.addAction("")
        self._tray_menu.addSeparator()
        self._tray_exit = self._tray_menu.addAction("")
        self._update_tray_menu()
        self._tray_open.triggered.connect(self._restore_from_tray)
        self._tray_exit.triggered.connect(QApplication.instance().quit)
        self._tray.setContextMenu(self._tray_menu)
        self._tray.activated.connect(self._on_tray_activated)

    def _update_tray_menu(self) -> None:
        s = STRINGS[self._lang]
        self._tray_open.setText(s["open"])
        self._tray_exit.setText(s["exit"])

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        self._tray.hide()
        self.showWindow.emit()
