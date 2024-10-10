# Generated by Django 5.0.7 on 2024-10-10 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0002_chatbot_character'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsCrawler',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collection_name', models.TextField(default='huffington')),
                ('news_url', models.URLField(default='https://huffpost.com')),
                ('url_icontains', models.CharField(default='/entry/', max_length=255)),
                ('article_tag', models.CharField(default='main', max_length=63)),
                ('article_id', models.CharField(default='main', max_length=63)),
            ],
        ),
    ]