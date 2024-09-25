from typing import TypeVar, Any
import uuid

from django.db import models


T = TypeVar("T")


def make_property_field(default_value: T) -> T:
    field_name = "field_" + str(uuid.uuid4())

    def set_default(self):
        if getattr(self, field_name, None) == None:
            setattr(self, field_name, default_value)

    def getter(self: models.Model) -> T:
        set_default(self)
        return getattr(self, field_name)

    def setter(self: models.Model, value: Any) -> None:
        setattr(self, field_name, value)

    return property(fget=getter, fset=setter)  # type:ignore
