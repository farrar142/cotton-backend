queue_name=${1:-celery}
celery -A base worker -B --loglevel=INFO -Q $queue_name