from django.contrib import admin

from .models import Plugin

class PluginAdmin(admin.ModelAdmin):
  actions = ["generate"]

  def generate(self, request, queryset):
    from trmnl.models import Device
    device = Device.objects.first()
    for obj in queryset.all():
        obj.create_screen(device)


admin.site.register(Plugin, PluginAdmin)