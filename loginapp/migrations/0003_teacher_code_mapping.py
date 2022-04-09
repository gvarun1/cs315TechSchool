# Generated by Django 4.0.1 on 2022-03-23 09:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courseapp', '0002_initial'),
        ('loginapp', '0002_otp_database'),
    ]

    operations = [
        migrations.CreateModel(
            name='TEACHER_CODE_MAPPING',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teacher_unique_code', models.CharField(max_length=8)),
                ('activation_status', models.BooleanField(default=False)),
                ('teacher_email', models.EmailField(max_length=254)),
                ('teacher_mapping', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='courseapp.available_courses')),
            ],
        ),
    ]
