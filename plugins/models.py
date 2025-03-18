import importlib
import logging
from django.db import models
from scheduler import job

from trmnl.models import Screen

logger = logging.getLogger("plugins")


# Plugin models that store reference to a plugin class. For instance a plugin named Pokemon Plugin with a description that
# store the reference to the PokemonPlugin class in whos-that-pokemon.plugin.PokemonPlugin. Then to use the plugin, we can
# instantiate the PokemonPlugin class and call the generate_html method to get the HTML content.
class Plugin(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    plugin_class = models.CharField(
        max_length=255, unique=True, help_text="Python path to the plugin class"
    )
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plugin"
        verbose_name_plural = "Plugins"

    def __str__(self):
        return self.name

    def get_plugin(self):
        module, class_name = self.plugin_class.rsplit(".", 1)
        plugin_class = getattr(importlib.import_module(module), class_name)
        return plugin_class(self.config)

    def generate_html(self):
        return self.get_plugin().generate_html()

    def create_screen(self, device):
        plugin_instance = self.get_plugin()
        html = plugin_instance.generate_html()
        screen = Screen.objects.create(device=device, html=html)
        screen.generate_screen()


# TODO : review jobs for now just metro ?
@job
def create_latest_screens():
    logger.info("Starting create_latest_screens job")
    from trmnl.models import Device

    device = Device.objects.first()
    plugins = Plugin.objects.filter(name="IDFM Métro").all()
    old_latest = device.screen_set.order_by("-created_at").first()
    for plugin in plugins:
        plugin.create_screen(device)
        old_latest.delete()
        logger.info(f"Screen created for plugin {plugin.name}")
    logger.info("Finished create_latest_screens job")
