# Generated by Django 5.1.7 on 2025-03-24 23:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trmnl', '0006_alter_playlist_weekdays'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlistitem',
            name='is_active',
            field=models.BooleanField(blank=True, default=True, verbose_name='Is active'),
        ),
        migrations.AddField(
            model_name='screen',
            name='playlist_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='screens', to='trmnl.playlistitem'),
        ),
        migrations.AlterField(
            model_name='playlist',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playlists', to='trmnl.device', verbose_name='Device'),
        ),
        migrations.AlterField(
            model_name='playlistitem',
            name='playlist',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='trmnl.playlist', verbose_name='Playlist'),
        ),
    ]
