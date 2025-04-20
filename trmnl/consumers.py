import base64
import json
import logging
import shutil
import tempfile
import time

from channels.generic.websocket import AsyncWebsocketConsumer
from playwright.async_api import async_playwright
from wand.image import Image

from byos_django import settings

logger = logging.getLogger(__name__)


class PreviewConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pw = None
        self.browser = None
        self.page = None

    async def connect(self):
        if not self.scope["user"].is_superuser:
            await self.close(reason="Unauthorized")
            return
        pw_manager = async_playwright()
        self.pw = await pw_manager.start()
        if settings.PW_SERVER:
            self.browser = await self.pw.firefox.connect(ws_endpoint=settings.PW_SERVER)
        else:
            self.browser = await self.pw.firefox.launch(
                headless=True,
                args=["--window-size=800,480", "--disable-web-security"],
            )
        await self.accept()
        logger.info(f"Connected: {self.scope['user']}")

    async def disconnect(self, close_code):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()
        self.page = None
        self.browser = None
        self.pw = None

    async def receive(self, text_data=None, bytes_data=None) -> None:
        text_data_json = json.loads(text_data)
        await self.send(
            text_data=json.dumps(await self.generate(text_data_json.get("html", None)))
        )

    async def generate(self, html):
        if not self.page:
            self.page = await self.browser.new_page()
            await self.page.set_viewport_size({"width": 800, "height": 480})
        start_time = time.time()
        if not html:
            return {"content": ""}

        # get random file name
        folder = tempfile.mkdtemp()

        await self.page.set_content(html)
        await self.page.evaluate(
            'document.getElementsByTagName("html")[0].style.overflow = "hidden";'
            'document.getElementsByTagName("body")[0].style.overflow = "hidden";'
        )
        await self.page.screenshot(path=f"/{folder}/screen.png")

        with Image(filename=f"/{folder}/screen.png") as img:
            img.transform_colorspace("gray")
            img.quantize(2, colorspace_type="gray", dither=True)
            img.type = "grayscale"
            img.save(filename=f"bmp3:/{folder}/screen.bmp")

        with open(f"/{folder}/screen.bmp", "rb") as f:
            # base64
            screen = f"data:image/bmp;base64,{base64.b64encode(f.read()).decode()}"

        # clean up
        shutil.rmtree(folder, ignore_errors=True)

        return (
            {
                "content": screen,
                "render_time": time.time() - start_time,
            },
        )
