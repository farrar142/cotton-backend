from collections import Counter, defaultdict
from datetime import datetime
import json
from typing import Generic, TypeVar, TypedDict

from django.utils.timezone import localtime

from commons.lock import get_redis


class LRUCache:
    def __init__(self, key: str, max_size: int):
        self.client = get_redis()
        self.key = key
        self.max_size = max_size

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.client.close()

    def trunc(self):
        self.client.delete(self.key)

    def all(self) -> list[int]:
        values = self.client.lrange(self.key, 0, -1)
        encoded = list(map(int, values))  # type:ignore
        return encoded

    def lpop(self, length: int = 1):
        return self.client.lpop(self.key, length)

    def add(self, *values: int):
        new_length = len(values)
        already = len(self.all())
        exceed = already + new_length - self.max_size
        if 0 < exceed:
            self.lpop(exceed)
        if self.max_size < new_length:
            values = values[new_length - self.max_size : new_length]
        self.client.rpush(self.key, *values)

    def counter(self):
        all = self.all()
        counter = Counter(all)
        return list(map(lambda x: x[0], sorted(counter.items(), key=lambda x: -x[1])))


T = TypeVar("T")


class ISOTime(datetime):
    @property
    def __dict__(self):
        return self.isoformat()

    def toJSON(self):
        return self.isoformat()


def dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__


class Container(TypedDict, Generic[T]):
    value: T
    weights: int
    created_at: ISOTime


class TimeoutCache(Generic[T]):

    def __init__(self, key: str):
        self.client = get_redis()
        self.key = key

    def remove_out_dated(self, expire: datetime):
        all = self.all()
        outdateds: list[Container[T]] = []
        for item in all:
            if item["created_at"] < expire:
                outdateds.append(item)

        for outdated in outdateds:
            self.client.lrem(self.key, 0, json.dumps(outdated, default=dumper))

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.client.close()

    def trunc(self):
        self.client.delete(self.key)

    def decode(self, value: str):
        loads = json.loads(value)
        loads["created_at"] = ISOTime.fromisoformat(loads["created_at"])
        return loads

    def all(self) -> list[Container[T]]:
        values = self.client.lrange(self.key, 0, -1)
        return list(map(self.decode, values))  # type:ignore

    def add(self, *values: T, weights=1):
        now = localtime().isoformat()
        date_wrapped = list(
            map(
                lambda x: json.dumps(dict(value=x, created_at=now, weights=weights)),
                values,
            )
        )
        self.client.rpush(self.key, *date_wrapped)

    def counter(self):
        all = self.all()
        res = defaultdict[T, int](int)
        for item in all:
            res[item["value"]] += item["weights"]
        sorted_res = sorted(res.items(), key=lambda x: -x[1])
        return list(map(lambda x: x[0], sorted_res))
