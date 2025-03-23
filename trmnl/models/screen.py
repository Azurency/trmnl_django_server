import base64
import logging
import shutil
import tempfile

from django.conf import settings
from django.db import models
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from playwright.sync_api import sync_playwright
from wand.image import Image

from utils.model_utils import TimeStampedModel

logger = logging.getLogger("trmnl")


class Screen(TimeStampedModel):
    device = models.ForeignKey("trmnl.Device", on_delete=models.CASCADE)
    html = models.TextField()
    screen = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    generated = models.BooleanField(default=False)

    def generate_screen(self):
        # get random file name
        folder = tempfile.mkdtemp()

        with sync_playwright() as p:
            if settings.PW_SERVER:
                browser = p.firefox.connect(ws_endpoint=settings.PW_SERVER)
            else:
                browser = p.firefox.launch(
                    headless=True,
                    args=["--window-size=800,480", "--disable-web-security"],
                )
            page = browser.new_page()
            page.set_viewport_size({"width": 800, "height": 480})

            # Render template with Django template engine
            template = get_template("screen.html")
            html = template.render({"content": mark_safe(self.html)})
            page.set_content(html)
            page.evaluate(
                'document.getElementsByTagName("html")[0].style.overflow = "hidden";'
                'document.getElementsByTagName("body")[0].style.overflow = "hidden";'
            )
            page.screenshot(path=f"/{folder}/screen.png")
            browser.close()

        with Image(filename=f"/{folder}/screen.png") as img:
            img.transform_colorspace("gray")
            img.quantize(2, colorspace_type="gray", dither=True)
            img.save(filename=f"bmp3:/{folder}/screen.bmp")

        with open(f"/{folder}/screen.bmp", "rb") as f:
            self.screen = f.read()
            self.generated = True
            self.save()

        # clean up
        shutil.rmtree(folder, ignore_errors=True)

    @property
    def image_as_base64(self):
        return f"data:image/bmp;base64,{base64.b64encode(self.screen).decode()}"

    @property
    def image_as_url_for_device(self):
        device_api_key = self.device.api_key
        return f"/api/v1/media/{self.device.friendly_id}-{self.id}.bmp?api_key={device_api_key}"

    @property
    def image_as_url_for_device_filename(self):
        return f"{self.device.friendly_id}-{self.id}.bmp"
