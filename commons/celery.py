from typing import Callable, Generic, ParamSpec, TypeVar
from celery import shared_task as st
from celery.result import AsyncResult
from celery.app.task import Task

T = TypeVar("T")
P = ParamSpec("P")


class TypeResult[T](Task):
    def get(self) -> T: ...


class TypedTask(Task, Generic[P, T]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T: ...
    def delay(self, *args: P.args, **kwargs: P.kwargs) -> TypeResult[T]: ...


def shared_task(*args, **kwargs) -> Callable[[Callable[P, T]], TypedTask[P, T]]:
    return st(*args, **kwargs)  # type:ignore
