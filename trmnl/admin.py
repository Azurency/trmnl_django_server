import json
import logging

from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import APIKey, Device, DeviceLog, Playlist, PlaylistItem, Screen

logger = logging.getLogger("trmnl")


class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "friendly_id",
        "device_name",
        "user",
        "refresh_rate",
        "last_seen_at",
    )
    list_filter = ("user", "created_at")
    search_fields = ("friendly_id", "device_name", "mac_address")
    list_editable = ("device_name", "user", "refresh_rate")

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        # Make all fields read-only except device_name and user
        editable_fields = {"device_name", "user", "refresh_rate"}
        all_fields = {field.name for field in self.model._meta.fields}
        readonly_fields = all_fields - editable_fields
        return readonly_fields


class DeviceLogAdmin(admin.ModelAdmin):
    list_display = ("device", "created_at")
    list_filter = ("device", "created_at")
    search_fields = ("device", "message")
    readonly_fields = ("device", "created_at", "message_pretty")
    fields = ("device", "created_at", "message_pretty")

    def message_pretty(self, obj=None):
        result = ""
        if obj and obj.message:
            result = json.dumps(obj.message, indent=4, sort_keys=True)
            # keep spaces
            result_str = f"<pre>{result}</pre>"
            result = mark_safe(result_str)
        return result

    message_pretty.short_description = "Message"


class ScreenAdmin(admin.ModelAdmin):
    list_display = ("device", "created_at", "generated")
    list_filter = ("device", "created_at", "generated")
    search_fields = ("device", "html")
    readonly_fields = ("created_at", "generated", "embed_image", "playlist_item")
    fields = (
        "device",
        "created_at",
        "generated",
        "html",
        "embed_image",
        "playlist_item",
    )
    actions = ["generate"]

    def embed_image(self, obj=None):
        result = ""
        if obj and obj.generated:
            result = f'<img src="{obj.image_as_base64}" alt="screen">'
        return mark_safe(result)

    embed_image.short_description = "Generated Image"

    def get_readonly_fields(self, request, obj=...):
        if obj and obj.generated:
            return ["created_at", "generated", "html", "embed_image", "playlist_item"]
        return ["created_at", "generated", "embed_image", "playlist_item"]

    def generate(self, request, queryset):
        objs = queryset.filter(generated=False)
        obj: Screen
        for obj in objs:
            obj.generate_screen()

    def save_model(self, request, obj, form, change):
        if not obj.generated:
            obj.generate_screen()
        super().save_model(request, obj, form, change)


class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "created_at")
    list_filter = ("user", "created_at")
    search_fields = ("name", "user__username")
    exclude = ("key",)

    def save_model(self, request, obj, form, change):
        if not obj.key:
            obj.save()
            # show message with key
            self.message_user(
                request,
                f"Your API Key is {obj.key}. It will not be shown again.",
                level=messages.SUCCESS,
            )
        super().save_model(request, obj, form, change)


class PlaylistAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "name",
        "device",
        "weekday_str",
        "active_from",
        "active_to",
        "is_active",
    )

    def weekday_str(self, obj):
        return obj.weekdays.to_str_list()

    weekday_str.short_description = _("Weekdays")

    readonly_fields = ("uuid", "created_at", "updated_at")
    search_fields = ("uuid", "device__friendly_id", "device__device_name")


class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = ("uuid", "playlist", "order", "plugin", "last_displayed_at")


admin.site.register(Device, DeviceAdmin)
admin.site.register(DeviceLog, DeviceLogAdmin)
admin.site.register(Screen, ScreenAdmin)
admin.site.register(APIKey, APIKeyAdmin)
admin.site.register(Playlist, PlaylistAdmin)
admin.site.register(PlaylistItem, PlaylistItemAdmin)
