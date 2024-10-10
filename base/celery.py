import os

from django.conf import settings

from celery import Celery, schedules

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
            "task": "ai.tasks.crawl_huffington_post",
            "schedule": schedules.crontab(
                hour="*", minute="0"
            ),  # 매시 정각에 실행되도록
            "args": (),
            "options": {"queue": "window"},
        },
        "chatbots_post": {
            "task": "ai.tasks.chatbots_post_about_news",
            "schedule": schedules.crontab(minute="*/5"),
            "args": (),
            "options": {"queue": "window"},
        },
    }
)
# Load task modules from all registered Django apps.
app.autodiscover_tasks()
