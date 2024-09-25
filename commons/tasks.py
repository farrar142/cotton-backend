from datetime import datetime, timezone
import time
from commons.celery import shared_task


@shared_task()
def debug_task():
    for _ in range(3):
        time.sleep(1)
    return datetime.now()
