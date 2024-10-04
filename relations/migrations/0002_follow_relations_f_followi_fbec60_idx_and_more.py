# Generated by Django 5.0.7 on 2024-10-04 18:36

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('relations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name='follow',
            index=models.Index(fields=['following_to', 'created_at'], name='relations_f_followi_fbec60_idx'),
        ),
        migrations.AddIndex(
            model_name='follow',
            index=models.Index(fields=['followed_by', 'created_at'], name='relations_f_followe_a148c1_idx'),
        ),
        migrations.AddIndex(
            model_name='follow',
            index=models.Index(fields=['following_to', 'followed_by'], name='relations_f_followi_d53864_idx'),
        ),
    ]
