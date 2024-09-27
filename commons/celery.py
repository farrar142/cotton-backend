from typing import Callable, Generic, ParamSpec, TypeVar
from celery import shared_task as st
from celery.result import AsyncResult
from celery.app.task import Task
from django.conf import settings

T = TypeVar("T")
P = ParamSpec("P")


class TypeResult(Task, Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value
        super().__init__()

    def get(self) -> T:
        return self.value


class TypedTask(Task, Generic[P, T]):
    def __init__(self, func: Callable[P, T]) -> None:
        self.func = func
        super().__init__()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.func(*args, **kwargs)

    def delay(self, *args: P.args, **kwargs: P.kwargs) -> TypeResult[T]:
        return TypeResult(self.func(*args, **kwargs))


def shared_task(*args, **kwargs) -> Callable[[Callable[P, T]], TypedTask[P, T]]:
    if settings.DEBUG:
        return TypedTask
    return st(*args, **kwargs)  # type:ignore
