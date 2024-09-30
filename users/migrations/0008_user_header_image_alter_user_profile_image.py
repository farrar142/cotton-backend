# Generated by Django 5.0.7 on 2024-09-29 09:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0003_image_created_at_alter_image_url'),
        ('users', '0007_alter_user_bio'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='header_image',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='header_users', to='images.image'),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_image',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profile_users', to='images.image'),
        ),
    ]