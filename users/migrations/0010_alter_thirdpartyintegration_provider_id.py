# Generated by Django 5.0.7 on 2024-10-08 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_thirdpartyintegration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thirdpartyintegration',
            name='provider_id',
            field=models.PositiveBigIntegerField(),
        ),
    ]
