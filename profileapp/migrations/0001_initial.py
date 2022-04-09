# Generated by Django 4.0.1 on 2022-03-22 10:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('loginapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='USER_PROFILE_DATABASE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_profile_photo', models.ImageField(default='E:\\Codes\\digi_school_django\\digischool_base\\digischool\\Templates/default_profile_photo.jpg', max_length=200, upload_to='')),
                ('user_signup_db_mapping', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='loginapp.user_signup_database')),
            ],
        ),
    ]