import os

from django.conf import settings

from celery import Celery, schedules
from kombu import Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base.settings")

app = Celery("base", broker=os.getenv("CACHE_HOST"), backend=os.getenv("CACHE_HOST"))

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object(f"django.conf:settings", namespace="CELERY")
app.conf.update(
    CELERY_BEAT_SCHEDULE={
        "crawl_news": {
            "task": "ai.tasks.crawl_news",
            "schedule": schedules.crontab(
                hour="8-20", minute="0"
            ),  # 매시 정각에 실행되도록
            "args": (),
        },
        "chatbots_post": {
            "task": "ai.tasks.chatbots_post_about_news",
            "schedule": schedules.crontab(minute="*/20", hour="9-20"),
            "args": (),
            "options": {"queue": "window"},
        },
        "expire_post_recommended": {
            "task": "posts.tasks.expire_post_recommended",
            "schedule": schedules.crontab(minute="*/1"),
        },
    }
)
app.conf.task_routes = {
    "django_elasticsearch_dsl.*": {"queue": "window"},
    "posts.dsl_processor.*": {"queue": "window"},
}
# Load task modules from all registered Django apps.
app.autodiscover_tasks()
