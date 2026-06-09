import asyncio
import os
from urllib.parse import urlparse

import aiohttp
from PySide6.QtCore import QObject, Signal

_MAX_CONCURRENT_DOWNLOADS = 20


class GetImage(QObject):
    progress_signal = Signal(int)
    max_value = Signal(int)
    # Передаёт ключ из strings.STRINGS (например "err_token") и доп. аргумент
    error = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.token: str = ""
        self.channel_id: str = ""
        self.output_folder: str = ""

    async def _fetch_messages(self, session: aiohttp.ClientSession, url: str) -> list[dict] | None:
        async with session.get(url, headers={"Authorization": self.token}) as response:
            if response.status == 200:
                return await response.json()
            match response.status:
                case 400 | 403 | 404:
                    self.error.emit("err_channel", "")
                case 401:
                    self.error.emit("err_token", "")
                case _:
                    self.error.emit("err_http", str(response.status))
            return None

    @staticmethod
    def _extract_attachments(messages: list[dict]) -> list[str]:
        return [
            proxy_url
            for msg in messages
            for attachment in msg.get("attachments", [])
            if (proxy_url := attachment.get("proxy_url"))
        ]

    async def _collect_image_urls(self, session: aiohttp.ClientSession) -> list[str] | None:
        base = f"https://discord.com/api/v9/channels/{self.channel_id}/messages"
        urls: list[str] = []

        messages = await self._fetch_messages(session, f"{base}?limit=100")
        if messages is None:
            return None
        if not messages:
            return urls

        urls.extend(self._extract_attachments(messages))
        last_id: str = messages[-1]["id"]

        # постранично собираем все сообщения канала
        while True:
            messages = await self._fetch_messages(session, f"{base}?before={last_id}&limit=100")
            if messages is None:
                return None
            if not messages:
                break
            urls.extend(self._extract_attachments(messages))
            last_id = messages[-1]["id"]

        return urls

    async def _download_one(
        self,
        session: aiohttp.ClientSession,
        sem: asyncio.Semaphore,
        url: str,
        idx: int,
        folder: str,
    ) -> bool:
        _, ext = os.path.splitext(urlparse(url).path)
        path = os.path.join(folder, f"image_{idx}{ext or '.jpg'}")
        async with sem:
            for _ in range(3):  # до 3 попыток на файл
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            try:
                                with open(path, "wb") as f:
                                    # Stream the response in chunks to avoid incomplete payload issues
                                    async for chunk in response.content.iter_chunked(65536):
                                        if not chunk:
                                            break
                                        f.write(chunk)
                            except (aiohttp.client_exceptions.ClientPayloadError, aiohttp.http_exceptions.ContentLengthError, asyncio.IncompleteReadError, ConnectionResetError):
                                # transient download error, retry
                                await asyncio.sleep(1)
                                continue
                            return True
                except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError):
                    # network-level error, retry
                    await asyncio.sleep(1)
                    continue
        return False

    async def _run(self) -> None:
        async with aiohttp.ClientSession() as session:
            urls = await self._collect_image_urls(session)
            if not urls:
                return
            folder = self.output_folder or "images"
            os.makedirs(folder, exist_ok=True)
            self.max_value.emit(len(urls))
            sem = asyncio.Semaphore(_MAX_CONCURRENT_DOWNLOADS)
            count = 0
            for coro in asyncio.as_completed([
                self._download_one(session, sem, url, idx, folder)
                for idx, url in enumerate(urls)
            ]):
                if await coro:
                    count += 1
                    self.progress_signal.emit(count)

    def start(self) -> None:
        asyncio.run(self._run())
