import os
from time import sleep
import redis


from django.test import TestCase
from django.core.cache import cache


class TestCommon(TestCase):
    def test_cache(self):
        key = "something"
        something = cache.get(key)
        self.assertEqual(something, None)

        something = cache.set(key, True)
        something = cache.get(key)
        self.assertEqual(something, True)

        cache.delete(key)
        something = cache.get(key)
        self.assertEqual(something, None)

    def test_redis(self):
        with redis.from_url(os.getenv("CACHE_HOST")) as client:
            key = "something"

            client.delete(key)

            something = client.get(key)
            self.assertEqual(something, None)

            client.set(key, 1)

            something = client.get(key)
            self.assertEqual(int(something), 1)  # type:ignore

            client.delete(key)

            something = client.get(key)
            self.assertEqual(something, None)

    def test_celery(self):
        from .tasks import debug_task

        debug_task()
        one = debug_task.delay()
        two = debug_task.delay()
        three = debug_task.delay()

        print(one.get(), two.get(), three.get())
