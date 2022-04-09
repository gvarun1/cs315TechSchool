# Generated by Django 4.0.1 on 2022-03-29 05:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lectureapp', '0002_all_video'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='all_lectures',
            name='yt_link_unique_id',
        ),
        migrations.AddField(
            model_name='all_lectures',
            name='lecture_datetime',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2022, 3, 29, 11, 28, 52, 314617)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='all_lectures',
            name='video_server_name',
            field=models.FileField(null=True, upload_to='videos/', verbose_name=''),
        ),
        migrations.DeleteModel(
            name='ALL_VIDEO',
        ),
    ]
