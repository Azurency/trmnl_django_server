# Generated by Django 5.1.7 on 2025-03-22 21:57

import django.db.models.deletion
import utils.weekday_field
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0005_plugin_uuid_alter_plugin_name_alter_plugin_recipe'),
        ('trmnl', '0004_alter_device_last_seen_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='apikey',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='devicelog',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='screen',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Public identifier')),
                ('is_active', models.BooleanField(blank=True, default=True, verbose_name='Is active')),
                ('weekdays', utils.weekday_field.WeekdaysField(choices=[(0, 'None'), (1, 'Monday'), (2, 'Tuesday'), (4, 'Wednesday'), (8, 'Thursday'), (16, 'Friday'), (32, 'Saturday'), (64, 'Sunday')])),
                ('active_from', models.TimeField(blank=True, null=True, verbose_name='Active from')),
                ('active_to', models.TimeField(blank=True, null=True, verbose_name='Active to')),
                ('refresh_interval', models.PositiveIntegerField(blank=True, default=900, verbose_name='Refresh interval')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trmnl.device', verbose_name='Device')),
            ],
            options={
                'verbose_name': 'Playlist',
                'verbose_name_plural': 'Playlists',
                'ordering': ['device', 'uuid'],
            },
        ),
        migrations.CreateModel(
            name='PlaylistItem',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Public identifier')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Order')),
                ('last_displayed_at', models.DateTimeField(blank=True, null=True, verbose_name='Last displayed at')),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trmnl.playlist', verbose_name='Playlist')),
                ('plugin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='plugins.plugin', verbose_name='Plugin')),
            ],
            options={
                'verbose_name': 'Playlist item',
                'verbose_name_plural': 'Playlist items',
                'ordering': ['playlist', 'order', 'uuid'],
            },
        ),
    ]
