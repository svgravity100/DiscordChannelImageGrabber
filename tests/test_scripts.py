import pytest
import aiohttp
from PySide6.QtTest import QSignalSpy
from scripts import GetImage


# ── unit-тесты (без сети) ─────────────────────────────────────────────────────

def test_extract_attachments_empty_list(qapp):
    assert GetImage._extract_attachments([]) == []


def test_extract_attachments_with_images(qapp):
    messages = [
        {"attachments": [{"proxy_url": "https://cdn.discord.com/img1.jpg"}]},
        {"attachments": [{"proxy_url": "https://cdn.discord.com/img2.png"}]},
        {"attachments": []},
        {},
    ]
    result = GetImage._extract_attachments(messages)
    assert result == [
        "https://cdn.discord.com/img1.jpg",
        "https://cdn.discord.com/img2.png",
    ]


def test_extract_attachments_multiple_in_one_message(qapp):
    messages = [{"attachments": [
        {"proxy_url": "https://cdn.discord.com/a.jpg"},
        {"proxy_url": "https://cdn.discord.com/b.jpg"},
    ]}]
    assert len(GetImage._extract_attachments(messages)) == 2


def test_extract_attachments_no_proxy_url(qapp):
    messages = [{"attachments": [{"url": "https://cdn.discord.com/img.jpg"}]}]
    assert GetImage._extract_attachments(messages) == []


# ── integration-тесты (требуют tests/.env) ────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_messages_valid_token(qapp, discord_token, discord_channel):
    obj = GetImage()
    obj.token = discord_token
    obj.channel_id = discord_channel
    spy = QSignalSpy(obj.error)
    async with aiohttp.ClientSession() as session:
        url = f"https://discord.com/api/v9/channels/{discord_channel}/messages?limit=5"
        result = await obj._fetch_messages(session, url)
    assert result is not None
    assert isinstance(result, list)
    assert spy.count() == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_messages_invalid_token(qapp, discord_channel):
    obj = GetImage()
    obj.token = "invalid_token_xyz"
    obj.channel_id = discord_channel
    spy = QSignalSpy(obj.error)
    async with aiohttp.ClientSession() as session:
        url = f"https://discord.com/api/v9/channels/{discord_channel}/messages?limit=5"
        result = await obj._fetch_messages(session, url)
    assert result is None
    assert spy.count() == 1
    assert spy.at(0)[0] == "err_token"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_messages_wrong_channel(qapp, discord_token):
    obj = GetImage()
    obj.token = discord_token
    obj.channel_id = "000000000000000000"
    spy = QSignalSpy(obj.error)
    async with aiohttp.ClientSession() as session:
        url = "https://discord.com/api/v9/channels/000000000000000000/messages?limit=5"
        result = await obj._fetch_messages(session, url)
    assert result is None
    assert spy.count() == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_collect_image_urls_returns_list(qapp, discord_token, discord_channel):
    obj = GetImage()
    obj.token = discord_token
    obj.channel_id = discord_channel
    spy = QSignalSpy(obj.error)
    async with aiohttp.ClientSession() as session:
        result = await obj._collect_image_urls(session)
    assert spy.count() == 0
    assert result is not None
    assert isinstance(result, list)
    for url in result:
        assert isinstance(url, str)
        assert url.startswith("http")
