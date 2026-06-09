import os
import pytest
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope="session")
def discord_token():
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        pytest.skip("DISCORD_TOKEN не задан в tests/.env")
    return token


@pytest.fixture(scope="session")
def discord_channel():
    channel = os.getenv("DISCORD_CHANNEL_ID", "").strip()
    if not channel:
        pytest.skip("DISCORD_CHANNEL_ID не задан в tests/.env")
    return channel
