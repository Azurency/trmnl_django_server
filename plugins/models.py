import importlib
import inspect
import logging
import sys
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from scheduler import job

from trmnl.models import Screen
from utils.model_utils import TimeStampedModel

from .utils import get_full_class_path

logger = logging.getLogger("plugins")


plugin_choices = [
    (get_full_class_path(y), x)
    for (x, y) in inspect.getmembers(sys.modules["plugins"], inspect.isclass)
]


class Plugin(TimeStampedModel):
    uuid = models.UUIDField(
        verbose_name=_("Public identifier"),
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    recipe = models.CharField(
        verbose_name=_("Recipe"),
        max_length=255,
        unique=True,
        help_text="Python fullpath to the recipe class",
        choices=plugin_choices,
    )
    config = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plugin"
        verbose_name_plural = "Plugins"

    def __str__(self):
        return self.name

    def get_recipe(self):
        module, class_name = self.recipe.rsplit(".", 1)
        recipe = getattr(importlib.import_module(module), class_name)
        return recipe(self.config)

    def generate_html(self):
        return self.get_recipe().generate_html()

    def create_screen(self, device):
        plugin_instance = self.get_recipe()
        html = plugin_instance.generate_html()
        screen = Screen.objects.create(device=device, html=html)
        screen.generate_screen()

