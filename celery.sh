queue_name=${1:-celery}
celery -A base worker --loglevel=INFO -Q $queue_name