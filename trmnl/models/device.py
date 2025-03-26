import datetime
import logging
import random
import re
import string

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from scheduler import job
from scheduler.models.task import Task, TaskArg, TaskType

from utils.model_utils import TimeStampedModel

logger = logging.getLogger("trmnl")


class Device(TimeStampedModel):
    friendly_id = models.CharField(max_length=6, unique=True, null=False, blank=False)
    device_name = models.CharField(max_length=50)
    mac_address = models.CharField(max_length=17, unique=True, null=False, blank=False)
    api_key = models.CharField(max_length=32, unique=True, null=False, blank=False)
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True, null=False, blank=False)
    last_seen_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    refreshes = models.IntegerField(default=0)
    refresh_rate = models.IntegerField(default=900)

    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        ordering = ["-created_at", "device_name"]

    def __str__(self):
        return f"{self.device_name} ({self.friendly_id})"

    def __repr__(self):
        return f"<Device: {self.device_name} ({self.friendly_id})>"

    @property
    def current_screen(self):
        return self.screen_set.order_by("-created_at").first()

    def clean(self):
        # Validate MAC Address format
        self.mac_address = self.mac_address.upper()
        if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", self.mac_address):
            raise ValidationError({"mac_address": "Invalid MAC address format."})

    def save(self, *args, **kwargs):
        # Generate a random API key on first create
        if not self.mac_address:
            # refuse to save the model if the MAC address is missing
            raise ValidationError({"mac_address": "MAC address is required."})
        if not self.api_key:
            self.api_key = "".join(random.choices(string.ascii_letters, k=32))
        # Generate a random friendly ID on first create
        if not self.friendly_id:
            self.friendly_id = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )

        self.clean()

        super().save(*args, **kwargs)

    def get_next_playlist_item(self):
        """Get the next item to display in the playlist."""
        playlists = self.playlists.filter(is_active=True)
        for playlist in playlists:
            if next_item := playlist.get_next_item():
                # get_next_item also checks if the playlist is active now
                return next_item
        return None

    def schedule_next_screen(self):
        """Schedule the next screen generation for this device."""
        next_playlist_item = self.get_next_playlist_item()
        if not next_playlist_item:
            logger.info(f"No active playlist found for device  #{self.id}")
            return
        current_screen = self.current_screen
        default_eta = timezone.now() + datetime.timedelta(seconds=5)
        eta = default_eta
        if current_screen:
            # Schedule the next screen generation n seconds before the current screen expires
            eta = (
                self.last_seen_at
                + datetime.timedelta(seconds=current_screen.display_duration)
                - datetime.timedelta(
                    seconds=settings.SCREEN_REFRESH_SECONDS_BEFORE_EXPIRY
                )
            )
            if eta < timezone.now():
                logger.info(
                    f"Screen already expired for device #{self.id}, scheduling now"
                )
                eta = default_eta
        else:
            logger.info(f"No screen found for device #{self.id}")
        # Create or update task (django-tasks-scheduler)
        task_identifier = (
            f"Screen Generation for Device {self.friendly_id} (#{self.id})"
        )
        (task, created) = Task.objects.update_or_create(
            name=task_identifier,
            task_type=TaskType.ONCE,
            callable="trmnl.models.device.generate_next_screen",
            defaults={
                "enabled": True,
                "queue": "default",
                "result_ttl": 1800,
                "scheduled_time": eta,
            },
        )
        if created:
            logger.info(f"Task created for device #{self.id} : {task}")
            # Add the device to task args
            TaskArg.objects.create(
                arg_type=TaskArg.ArgType.INT,
                val=self.id,
                object_id=task.id,
                content_object=task,
                content_type=ContentType.objects.get_for_model(task),
            )
        else:
            logger.info(f"Task updated for device #{self.id} : {task}")

    def get_screen(self, update_last_seen=False):
        if update_last_seen:
            self.last_seen_at = timezone.now()
            self.refreshes += 1
            self.save()
        return self.current_screen


class DeviceLog(TimeStampedModel):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    message = models.JSONField()

    class Meta:
        verbose_name = _("Device Log")
        verbose_name_plural = _("Device Logs")
        ordering = ["-created_at", "device"]


class APIKey(TimeStampedModel):
    name = models.CharField(max_length=50, null=False, blank=False)
    key = models.CharField(max_length=32, unique=True, null=False, blank=False)
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=False, blank=False
    )

    class Meta:
        verbose_name = _("API Key")
        verbose_name_plural = _("API Keys")
        ordering = ["-created_at", "name"]

    def __str__(self):
        return f"{self.name} (Owner: {self.user.username})"

    def __repr__(self):
        return f"<API Key: {self.name} (Owner: {self.user.username})>"

    def save(self, *args, **kwargs):
        # Generate a random API key on first create
        if not self.key:
            self.key = "".join(random.choices(string.ascii_letters, k=32))
        super().save(*args, **kwargs)


################
## Device Job ##
################


@job
def generate_next_screen(device_id: int):
    logger.info(f"Generating next screen for device #{device_id}")
    device = Device.objects.get(pk=device_id)
    playlist_item = device.get_next_playlist_item()
    if not playlist_item:
        logger.info(f"No active playlist found for device #{device_id}")
        return
    screen = playlist_item.generate_screen(True)
    logger.info(f"Generated screen #{screen.id} for device #{device_id}")
