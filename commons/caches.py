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
    v: T  # value
    w: int  # weights
    c: int  # created_at #minute


# 캐시크기의 경량화를 위해 필드이름을 줄이고, created_at을 특정 시간부터의 분, 혹은 시단위의 값으로 바꿀 수 있을 것 같음
pivot_time_minute = int(datetime(year=2024, month=1, day=1).timestamp() / 60)


class TimeoutCache(Generic[T]):

    def __init__(self, key: str):
        self.client = get_redis()
        self.key = key

    _pivot_time_minute: int | None = None

    @property
    def pivot_time_minute(self):
        if not self._pivot_time_minute:
            self._pivot_time_minute = self.minute_timestamp(
                datetime(year=2024, month=1, day=1)
            )
        return self._pivot_time_minute

    @staticmethod
    def minute_timestamp(dt: datetime):
        return int(dt.timestamp() / 60)

    def remove_out_dated(self, expire: datetime, min_items_count=100):
        expire_minute = self.minute_timestamp(expire) - self.pivot_time_minute
        all = self.all()
        outdateds: list[Container[T]] = []
        for item in all:
            if item["c"] < expire_minute:
                outdateds.append(item)

        current_size = all.__len__()  # 120
        removal_size = current_size - min_items_count  # 20
        if 0 < removal_size:
            outdateds = outdateds[:removal_size]

            for outdated in outdateds:
                self.client.lrem(self.key, 0, json.dumps(outdated, default=dumper))

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.client.close()

    def trunc(self):
        self.client.delete(self.key)

    def decode(self, value: str) -> Container[T]:
        loads: Container[T] = json.loads(value)
        return loads

    def all(self) -> list[Container[T]]:
        values = self.client.lrange(self.key, 0, -1)
        return list(map(self.decode, values))  # type:ignore

    def add(self, *values: T, weights=1, created_at: datetime | None = None):
        if created_at == None:
            created_at = localtime()
        c = self.minute_timestamp(created_at) - self.pivot_time_minute
        date_wrapped = list(
            map(
                lambda x: json.dumps(dict(v=x, c=c, w=weights)),
                values,
            )
        )
        self.client.rpush(self.key, *date_wrapped)

    def counter(self):
        all = self.all()
        res = defaultdict[T, int](int)
        for item in all:
            res[item["v"]] += item["w"]
        sorted_res = sorted(res.items(), key=lambda x: -x[1])
        return list(map(lambda x: x[0], sorted_res))
