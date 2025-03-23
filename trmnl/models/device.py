import logging
import random
import re
import string

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

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

    def __str__(self):
        return f"{self.device_name} ({self.friendly_id})"

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

    def get_screen(self, update_last_seen=False):
        screen = self.screen_set.order_by("-created_at").first()
        if update_last_seen:
            self.last_seen_at = timezone.now()
            self.refreshes += 1
            self.save()

        if screen:
            return screen

        return None


class DeviceLog(TimeStampedModel):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    message = models.JSONField()


class APIKey(TimeStampedModel):
    name = models.CharField(max_length=50, null=False, blank=False)
    key = models.CharField(max_length=32, unique=True, null=False, blank=False)
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=False, blank=False
    )

    def save(self, *args, **kwargs):
        # Generate a random API key on first create
        if not self.key:
            self.key = "".join(random.choices(string.ascii_letters, k=32))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Owner: {self.user.username})"
