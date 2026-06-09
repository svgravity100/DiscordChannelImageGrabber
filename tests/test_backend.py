import pytest
from PySide6.QtCore import QSettings
from PySide6.QtTest import QSignalSpy, QTest
from backend import Backend
from strings import STRINGS


@pytest.fixture(autouse=True)
def clean_settings():
    s = QSettings("DiscordImageGrabber", "App")
    s.clear()
    yield
    s.clear()


@pytest.fixture
def backend(qapp):
    return Backend()


# ── язык ──────────────────────────────────────────────────────────────────────

def test_default_language_is_valid(backend):
    assert backend.lang in ("en", "ru")


def test_strings_matches_current_language(backend):
    assert backend.strings == STRINGS[backend.lang]


def test_toggle_language_changes(backend):
    initial = backend.lang
    backend.toggleLanguage()
    assert backend.lang != initial


def test_toggle_language_returns_to_initial(backend):
    initial = backend.lang
    backend.toggleLanguage()
    backend.toggleLanguage()
    assert backend.lang == initial


def test_toggle_emits_strings_changed(backend):
    spy = QSignalSpy(backend.stringsChanged)
    backend.toggleLanguage()
    assert spy.count() == 1


def test_toggle_emits_folder_changed(backend):
    spy = QSignalSpy(backend.folderChanged)
    backend.toggleLanguage()
    assert spy.count() == 1


def test_toggle_emits_progress_changed(backend):
    spy = QSignalSpy(backend.progressChanged)
    backend.toggleLanguage()
    assert spy.count() == 1


def test_language_saved_to_settings(backend):
    backend.toggleLanguage()
    s = QSettings("DiscordImageGrabber", "App")
    assert s.value("lang") == backend.lang


def test_language_loaded_from_settings_ru(qapp):
    QSettings("DiscordImageGrabber", "App").setValue("lang", "ru")
    assert Backend().lang == "ru"


def test_language_loaded_from_settings_en(qapp):
    QSettings("DiscordImageGrabber", "App").setValue("lang", "en")
    assert Backend().lang == "en"


# ── токен ─────────────────────────────────────────────────────────────────────

def test_saved_token_empty_by_default(backend):
    assert backend.savedToken == ""


def test_saved_token_strips_whitespace(qapp):
    QSettings("DiscordImageGrabber", "App").setValue("token", "  my_token\n")
    assert Backend().savedToken == "my_token"


# ── папка ─────────────────────────────────────────────────────────────────────

def test_folder_display_without_folder(backend):
    backend._folder = ""
    assert backend.folderDisplay == STRINGS[backend.lang]["no_folder"]


def test_folder_display_with_folder(backend, tmp_path):
    backend._folder = str(tmp_path)
    assert backend.folderDisplay == tmp_path.name


def test_folder_display_changes_on_language_toggle(backend):
    backend._folder = ""
    backend._lang = "en"
    display_en = backend.folderDisplay
    backend._lang = "ru"
    display_ru = backend.folderDisplay
    assert display_en != display_ru


# ── прогресс ──────────────────────────────────────────────────────────────────

def test_progress_text_while_collecting(backend):
    backend._total = 0
    assert backend.progressText == STRINGS[backend.lang]["collecting"]


def test_progress_text_with_numbers(backend):
    backend._progress = 7
    backend._total = 20
    assert backend.progressText == "7 / 20"


def test_downloading_false_by_default(backend):
    assert backend.downloading is False


def test_progress_zero_by_default(backend):
    assert backend.progress == 0
    assert backend.total == 0


# ── воркер / сигналы прогресса ────────────────────────────────────────────────

def test_on_max_value_updates_total(backend):
    spy = QSignalSpy(backend.progressChanged)
    backend._on_max_value(42)
    assert backend.total == 42
    assert spy.count() == 1


def test_on_progress_updates_progress(backend):
    spy = QSignalSpy(backend.progressChanged)
    backend._on_progress(10)
    assert backend.progress == 10
    assert spy.count() == 1


def test_on_started_sets_downloading(backend):
    spy_dl = QSignalSpy(backend.downloadingChanged)
    spy_pr = QSignalSpy(backend.progressChanged)
    backend._pending_token = "tok"
    backend._on_started()
    assert backend.downloading is True
    assert backend.progress == 0
    assert backend.total == 0
    assert spy_dl.count() == 1
    assert spy_pr.count() == 1
    backend._downloading = False


def test_on_finished_resets_downloading(backend):
    backend._downloading = True
    backend._pending_token = "tok"
    spy = QSignalSpy(backend.downloadingChanged)
    backend._on_finished()
    assert backend.downloading is False
    assert spy.count() == 1
