from rest_framework.pagination import (
    CursorPagination as _CursorPagination,
    PageNumberPagination as _PageNumberPagination,
)


class CursorPagination(_CursorPagination):
    ordering = "-id"


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
