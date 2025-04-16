import logging
import uuid
from typing import Optional

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.model_utils import TimeStampedModel
from utils.weekday_field import Weekday, WeekdaysField

logger = logging.getLogger("trmnl")


class Playlist(TimeStampedModel):
    uuid = models.UUIDField(
        verbose_name=_("Public identifier"),
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )
    name = models.CharField(verbose_name=_("Name"), max_length=50, blank=True)
    device = models.ForeignKey(
        "trmnl.Device",
        verbose_name=_("Device"),
        on_delete=models.CASCADE,
        related_name="playlists",
    )
    is_active = models.BooleanField(
        verbose_name=_("Is active"), default=True, blank=True
    )
    weekdays = WeekdaysField(default=["0"], null=False, blank=False)
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
        return f"{self.device} - {self.name or self.uuid}"

    def __repr__(self):
        return f"<Playlist: {self.device} - {self.uuid}>"

    def is_active_now(self) -> bool:
        if not self.is_active:
            return False
        current_weekday = Weekday(timezone.now().isoweekday())
        if current_weekday not in self.weekdays:
            return False
        if self.active_from is None or self.active_to is None:
            return True
        current_time = timezone.now().time()
        return self.active_from <= current_time <= self.active_to

    def get_next_item(self) -> Optional["PlaylistItem"]:
        """
        Get the next item to display in the playlist.
        How it works:
        - If the playlist is not active, return None
        - If the playlist has no items, return None
        - If no item has been displayed yet, return the first item
        - Otherwise, return the first item with an order higher than the last displayed item
        - If no such item exists, return the first item
        :return: The next item to display or None
        """
        if not self.is_active_now():
            return None
        items = self.items.filter(is_active=True).order_by("order")
        if not items.exists():
            return None
        # Find the last displayed item
        last_displayed_item = (
            items.order_by("-last_displayed_at")
            .exclude(last_displayed_at__isnull=True)
            .first()
        )
        if last_displayed_item is None:
            return items.first()
        # Find the next item to display
        current_order = last_displayed_item.order
        next_item = items.filter(order__gt=current_order).first()
        if next_item is None:
            return items.first()
        return next_item


class PlaylistItem(TimeStampedModel):
    uuid = models.UUIDField(
        verbose_name=_("Public identifier"),
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )
    playlist = models.ForeignKey(
        "trmnl.Playlist",
        verbose_name=_("Playlist"),
        on_delete=models.CASCADE,
        related_name="items",
    )
    order = models.PositiveIntegerField(verbose_name=_("Order"), default=0)
    plugin = models.ForeignKey(
        "plugins.Plugin", verbose_name=_("Plugin"), on_delete=models.CASCADE
    )
    # In the future, could add groups to allow for multiple plugins to be displayed at once
    last_displayed_at = models.DateTimeField(
        verbose_name=_("Last displayed at"), blank=True, null=True
    )
    is_active = models.BooleanField(
        verbose_name=_("Is active"), default=True, blank=True
    )
    duration = models.PositiveIntegerField(
        verbose_name=_("Duration"),
        default=900,
        blank=True,
        help_text=_("In seconds"),
    )

    class Meta:
        verbose_name = _("Playlist item")
        verbose_name_plural = _("Playlist items")
        ordering = ["playlist", "order", "uuid"]

    def __str__(self):
        return f"{self.playlist} - {self.plugin.name} ({self.uuid})"

    def __repr__(self):
        return f"<PlaylistItem: {self.playlist} - {self.uuid}>"

    def generate_screen(self, update_last_displayed_at: bool = True):
        """Generate a screen for this playlist item."""
        screen = self.plugin.create_screen(self.playlist.device, playlist_item=self)
        if update_last_displayed_at:
            self.last_displayed_at = timezone.now()
            self.save()
        return screen
