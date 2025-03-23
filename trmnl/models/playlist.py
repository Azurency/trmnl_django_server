import logging
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.model_utils import TimeStampedModel
from utils.weekday_field import WeekdaysField

logger = logging.getLogger("trmnl")


class Playlist(TimeStampedModel):
    uuid = models.UUIDField(
        verbose_name=_("Public identifier"),
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )
    device = models.ForeignKey(
        "trmnl.Device", verbose_name=_("Device"), on_delete=models.CASCADE
    )
    is_active = models.BooleanField(
        verbose_name=_("Is active"), default=True, blank=True
    )
    weekdays = WeekdaysField(default=0, null=False, blank=False)
    active_from = models.TimeField(verbose_name=_("Active from"), blank=True, null=True)
    active_to = models.TimeField(verbose_name=_("Active to"), blank=True, null=True)
    refresh_interval = models.PositiveIntegerField(
        verbose_name=_("Refresh interval"), default=900, blank=True
    )

    class Meta:
        verbose_name = _("Playlist")
        verbose_name_plural = _("Playlists")
        ordering = ["device", "uuid"]

    def __str__(self):
        return f"{self.device} - {self.uuid}"

    def __repr__(self):
        return f"<Playlist: {self.device} - {self.uuid}>"


class PlaylistItem(TimeStampedModel):
    uuid = models.UUIDField(
        verbose_name=_("Public identifier"),
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )
    playlist = models.ForeignKey(
        "trmnl.Playlist", verbose_name=_("Playlist"), on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(verbose_name=_("Order"), default=0)
    plugin = models.ForeignKey(
        "plugins.Plugin", verbose_name=_("Plugin"), on_delete=models.CASCADE
    )
    # In the future, could add groups to allow for multiple plugins to be displayed at once
    last_displayed_at = models.DateTimeField(
        verbose_name=_("Last displayed at"), blank=True, null=True
    )

    class Meta:
        verbose_name = _("Playlist item")
        verbose_name_plural = _("Playlist items")
        ordering = ["playlist", "order", "uuid"]

    def __str__(self):
        return f"{self.playlist} - {self.uuid}"

    def __repr__(self):
        return f"<PlaylistItem: {self.playlist} - {self.uuid}>"
