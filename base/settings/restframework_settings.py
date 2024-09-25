REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "commons.authentication.CustomJWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "commons.paginations.CursorPagination",
    "PAGE_SIZE": 10,
    "EXCEPTION_HANDLER": "commons.exception_handlers.custom_exception_handler",
}
