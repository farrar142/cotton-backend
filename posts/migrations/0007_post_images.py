# Generated by Django 5.0.7 on 2024-09-27 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0002_image_large'),
        ('posts', '0006_alter_post_blocks'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='images',
            field=models.ManyToManyField(to='images.image'),
        ),
    ]
