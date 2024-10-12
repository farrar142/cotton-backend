from functools import wraps
import redis, os
from typing import Generic, TypeVar, ParamSpec, Callable

import redis.lock

T = TypeVar("T")
P = ParamSpec("P")


def get_redis():
    return redis.from_url(os.getenv("CACHE_HOST"))


def _with_lock(key: str | Callable[P, str], blocking_timeout: int | None = None):
    if blocking_timeout == None:
        blocking_timeout = 5

    def decorator(func: Callable[P, T]):

        def wrapper(*args: P.args, **kwargs: P.kwargs):

            _key = key if isinstance(key, str) else key(*args, **kwargs)
            with redis.from_url(os.getenv("CACHE_HOST")) as client:
                with client.lock(name=_key, blocking_timeout=5):
                    return func(*args, **kwargs)

        return wrapper

    return decorator


class with_lock(Generic[P, T]):
    lock: redis.lock.Lock

    def __init__(
        self, key: str | Callable[P, str], blocking_timeout: int | None = None
    ):
        self.blocking_timeout = 5 if blocking_timeout == None else blocking_timeout
        self.blocking_timeout = blocking_timeout
        self.key = key

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            key = self.key if isinstance(self.key, str) else self.key(*args, **kwargs)
            with get_redis() as client:
                with client.lock(name=key, blocking_timeout=self.blocking_timeout):
                    return func(*args, **kwargs)

        return wrapper

    def __enter__(self):
        key = self.key if isinstance(self.key, str) else ""
        self.client = get_redis()
        self.lock = self.client.lock(name=key, blocking_timeout=self.blocking_timeout)
        self.lock.__enter__()
        return self.lock

    def __exit__(self, *args, **kwargs):
        self.lock.__exit__(*args, **kwargs)
        self.client.close()
