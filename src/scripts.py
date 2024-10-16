import aiohttp
import asyncio
import requests
import os
from PyQt6.QtCore import QObject, pyqtSignal


class GetImage(QObject):
    LIST_IMAGES = 100
    progress_signal = pyqtSignal(int)
    max_value = pyqtSignal(int)
    error = pyqtSignal(str)
    output_folder = 0

    def __init__(self):
        super().__init__()
        self._token = None
        self._channel_id = None
        self.proxy_urls = []
        self._output_folder = None
    @property
    def token(self):
        return self._token
    
    @token.setter
    def token(self, value):
         self._token = value
    @property
    def channel_id(self):
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value):
        self._channel_id = value

    def get_url_image(self):
        url_base = f"https://discord.com/api/v9/channels/{
            self.channel_id}/messages?limit=100"
        response = requests.get(
            url_base, headers={"Authorization": self.token})
        print(response.status_code)
        match response.status_code:
            case 200:
                user_data = response.json()
                id = user_data[-1]["id"]
                for item in user_data:
                    if "attachments" in item and item["attachments"]:
                        for attachment in item["attachments"]:
                            if "proxy_url" in attachment:
                                self.proxy_urls.append(attachment["proxy_url"])
                return id
            case 400:
                self.handle_error("The channel field is incorrectly entered.")
            case 401:
                self.handle_error("Invalid Token.")
            case _:
                self.handle_error("Error: " + str(response.status_code))

    def get_irl_before(self, id=None) -> list:
        while True:
            url_base = f"https://discord.com/api/v9/channels/{
                self.channel_id}/messages?before={id}&limit=100"
            response = requests.get(
                url_base, headers={"Authorization": self.token})
            if response.status_code == 200:
                user_data = response.json()
                for item in user_data:
                    if "attachments" in item and item["attachments"]:
                        for attachment in item["attachments"]:
                            if "proxy_url" in attachment:
                                self.proxy_urls.append(attachment["proxy_url"])
                try:
                    id = user_data[-1]["id"]
                except IndexError:
                    break
        print(len(self.proxy_urls))
        self.max_value.emit(len(self.proxy_urls))
        return self.proxy_urls

    async def download_images(self, image_urls: list) -> None:
        self.count = 0
        if not self.output_folder:
            self.output_folder = "image"
        os.makedirs(self.output_folder, exist_ok=True)
        async with aiohttp.ClientSession() as session:
            tasks = []
            for idx, url in enumerate(image_urls):
                task = self.download_image(session, url, idx)
                tasks.append(task)
            await asyncio.gather(*tasks)

    async def download_image(self, session, url, idx):
        for _ in range(3):
            async with session.get(url) as response:

                if response.status == 200:
                    image_name = f"image_{idx}.jpg"
                    image_path = os.path.join(self.output_folder, image_name)
                    with open(image_path, "wb") as file:
                        file.write(await response.content.read())
                    self.count = self.count + 1
                    self.progress_signal.emit(self.count)
                    return
                else:
                    await asyncio.sleep(1)

    def start(self):
        asyncio.run(self.download_images(
            self.get_irl_before(self.get_url_image())))

    def handle_error(self, message):
        self.error.emit(message)
        print(message)



