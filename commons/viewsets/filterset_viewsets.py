from datetime import datetime
from rest_framework import exceptions
from typing import Optional, Iterable, Callable, TypeVar, Generic, Union

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet, Model, Q

from ..requests import Request


T = TypeVar("T", bound=Model)
U = TypeVar("U", bound=AbstractBaseUser)

QueryStr = Union[list[str], str, bool]


class CustomFiltersetMixin(Generic[T, U]):
    request: Request[U]
    exclude_fields: Optional[Iterable[str]] = []
    filterset_fields: Optional[Iterable[str]] = None
    filterset_num_fields: Optional[Iterable[str]] = None
    filterset_datetime_fields: Optional[Iterable[str]] = None
    filterset_boolean_fields: Optional[Iterable[str]] = None
    search_fields: Optional[Iterable[str]] = None
    ordering_fields: Optional[Iterable[str]] = None
    distinct: bool = True

    @property
    def number_fields(self):
        return ("__gte", "__lte", "__lt", "__gt")

    def aware_error(self, func: Callable, *args, **kwargs):
        try:
            func(*args, **kwargs)
            return True
        except Exception as e:
            return False

    query_params: Optional[Iterable[tuple[str, str]]] = None

    def get_filterset(
        self,
        targets: Iterable[str] | None = None,
        type: Union[type[str], type[int], type[bool], type[datetime]] = str,
    ):
        queries = {}
        if not self.query_params:
            self.query_params = list(self.request.query_params.items())
        for key, val in self.query_params:
            if key == "ordering":
                continue
            if key in ["cursor", "search", "page"]:
                continue
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            if key.endswith("__in"):
                if val == None:
                    continue
                if isinstance(val, str):
                    val = list(filter(lambda x: x.strip() != "", val.split(",")))
            if val == None:
                continue
            if targets == "*":
                queries[key] = val
            elif targets and key in targets:
                if type == int:
                    validate_integer_val(key, val)
                elif type == datetime:
                    validate_datetime_val(key, val)
                elif type == bool:
                    validate_bool_val(key, val)

                if key.endswith("__isnot"):
                    key = key.removesuffix("__isnot")
                    queries[key] = val
                else:
                    queries[key] = val
        return queries

    def get_search_queryset(self, targets: Iterable[str] | None):
        if not targets:
            return None
        a: Optional[Q] = None
        for key, val in self.request.query_params.items():
            if key == "search":
                for target in targets:
                    if not a:
                        a = Q(**{f"{target}__icontains": val})
                    else:
                        a = a | Q(**{f"{target}__icontains": val})
        return a

    def filter_queryset(self, queryset: QuerySet[T]):
        queries = self.get_filterset(self.filterset_fields)
        num_queries = self.get_filterset(self.filterset_num_fields, int)
        date_queries = self.get_filterset(self.filterset_datetime_fields, datetime)
        boolean_queries = self.get_filterset(self.filterset_boolean_fields, bool)
        ex_queries = self.get_filterset(self.exclude_fields)
        search_queries = self.get_search_queryset(self.search_fields)
        if search_queries != None:
            queryset = queryset.filter(search_queries)
        qs = queryset.filter(
            **queries, **num_queries, **date_queries, **boolean_queries
        ).exclude(**ex_queries)
        for key, val in self.request.query_params.items():
            if key == "ordering":
                if self.ordering_fields and val in self.ordering_fields:
                    qs = qs.order_by(val)
                continue
        if self.distinct:
            return qs.distinct()
        return qs


def get_query_exception_message(key: str, val, type="숫자"):
    return {key: f"{key}는 {type}여야 됩니다.값 {val}은 유효한 값이 아닙니다."}


def validate_integer_val(key: str, val: QueryStr):
    if isinstance(val, list):
        # 하나라도 숫자가 될 수 없는 요소가 있다면
        if any(map(lambda x: not x.lstrip("+-").isdigit(), val)):
            raise exceptions.ValidationError(get_query_exception_message(key, val))
    elif isinstance(val, bool):
        raise exceptions.ValidationError(get_query_exception_message(key, val))
    else:
        if not val.lstrip("+-").isdigit():
            raise exceptions.ValidationError(get_query_exception_message(key, val))


def validate_datetime_val(key: str, val: QueryStr):
    if not isinstance(val, str):
        raise exceptions.ValidationError(
            get_query_exception_message(key, val, "ISO포맷")
        )
    try:
        datetime.fromisoformat(val)
    except:
        raise exceptions.ValidationError(
            get_query_exception_message(key, val, "ISO포맷")
        )


def validate_bool_val(key: str, val: QueryStr):
    if not isinstance(val, bool):
        raise exceptions.ValidationError(get_query_exception_message(key, val))
    try:
        bool(val)
    except:
        raise exceptions.ValidationError(get_query_exception_message(key, val))
