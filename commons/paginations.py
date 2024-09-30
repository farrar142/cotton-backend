from typing import Literal
from django.db import models
from rest_framework.pagination import (
    CursorPagination as _CursorPagination,
    PageNumberPagination as _PageNumberPagination,
    LimitOffsetPagination,
    BasePagination,
)
from rest_framework.response import Response
from commons.requests import Request


class CursorPagination(_CursorPagination):
    ordering = "-id"

    def get_ordering(self, request, queryset, view):
        if hasattr(view, "ordering"):
            return view.ordering  # type:ignore
        return super().get_ordering(request, queryset, view)


class PageNumberPagination(_PageNumberPagination):
    ordering = "-id"

    def get_total_page(self):
        count = self.page.paginator.count
        page_size = int(self.get_page_size(self.request))  # type:ignore
        page_count, left_count = count // page_size, count % page_size
        if 0 < left_count:
            return page_count + 1
        return page_count

    def get_paginated_response(self, data):
        from rest_framework.response import Response

        return Response(
            {
                "count": self.page.paginator.count,
                "total_page": self.get_total_page(),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class TimelinePagination(BasePagination):
    offset_field = "id"
    offset_order: Literal["desc"] | Literal["asc"] = "desc"
    queryset: models.QuerySet

    def get_current_offset(self, request: Request):
        return request.query_params.get("current_offset")

    def get_direction(self, request: Request):
        direction = request.query_params.get("direction", "next")
        if direction == "prev":
            return "__gt"
        else:
            return "__lte"

    def get_offset_field(self, request: Request, view):

        return getattr(view, "offset_field", self.offset_field)

    def get_offset_order(self, request: Request, view):
        if self.offset_order == "desc":
            return f"-"
        return ""

    def paginate_queryset(self, queryset, request, view=None):
        self._currentOffset = self.get_current_offset(request)
        self._direction = self.get_direction(request)
        self._offset_field = self.get_offset_field(request, view)
        self._offset_order = self.get_offset_order(request, view)
        query_params = {f"{self._offset_field}{self._direction}": self._currentOffset}
        if not self._currentOffset:
            query_params = {}
        self.queryset = queryset.filter(**query_params).order_by(
            f"{self._offset_order}{self._offset_field}", f"{self._offset_order}id"
        )
        self.sliced_queryset = self.queryset[0:10]
        return self.sliced_queryset

    def get_response_current_offset(self, data):
        if not data:
            return None
        if not isinstance(data[0], dict):
            return None
        return data[0].get(self._offset_field, None)

    def get_has_next(self):
        if self.queryset.count() <= self.sliced_queryset.count():
            return False
        return True

    def get_paginated_response(self, data):
        return Response(
            {
                "has_prev": None,
                "has_next": self.get_has_next(),
                "results": data,
                "current_offset": self.get_response_current_offset(data),
                "offset_field": self._offset_field,
            }
        )
