from dataclasses import dataclass
from functools import wraps
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    ParamSpec,
    Self,
    TypeVar,
    TypedDict,
    Union,
)

from typing import Generic, ParamSpec, TypeVar, Callable


class PlainText:
    type: str
    value: str

    def json(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def parse(cls, text: dict):
        return cls(**text)


@dataclass
class Text(PlainText):
    value: str
    type: Literal["text"] = "text"

    def json(self):
        return dict(value=self.value, type=self.type)


@dataclass
class Hyperlink(PlainText):
    value: str
    url: str
    type: Literal["hyperlink"] = "hyperlink"

    def json(self):
        return dict(value=self.value, type=self.type, url=self.url)


@dataclass
class Mention(PlainText):
    value: str
    user_id: int
    type: Literal["mention"] = "mention"

    def json(self):
        return dict(value=self.value, type=self.type, user_id=self.user_id)


@dataclass
class Hidden(PlainText):
    value: str
    type: Literal["hidden"] = "hidden"


class JsonData(TypedDict):
    builder_type: str
    value: list[dict]


T = TypeVar("T", bound=PlainText)
P = ParamSpec("P")


class BlockTextBuilder:
    builder_type: Literal["block_text"] = "block_text"
    text_list: list[PlainText]

    def __init__(self):
        self.text_list = []

    def text_wrapper(self, kls: Callable[P, T]):
        def decorator(*args: P.args, **kwargs: P.kwargs) -> "BlockTextBuilder":
            text = kls(*args, **kwargs)
            self.text_list.append(text)
            return self

        return decorator

    @property
    def text(self):
        return self.text_wrapper(Text)

    @property
    def hyperlink(self):
        return self.text_wrapper(Hyperlink)

    @property
    def mention(self):
        return self.text_wrapper(Mention)

    @property
    def hidden(self):
        return self.text_wrapper(Hidden)

    def get_plain_text(self):
        return "".join(list(map(lambda x: x.value, self.text_list)))

    def get_json(self):
        return JsonData(
            value=list(map(lambda text: text.json(), self.text_list)),
            builder_type="block_text",
        )

    @classmethod
    def _get_matched_type(cls, text_type: str) -> type[Text] | None:
        texts: list[type[Text]] = [Text, Hyperlink, Mention, Hidden]  # type:ignore
        return next(filter(lambda x: x.type == text_type, texts), None)

    @classmethod
    def parse_json(cls, data: JsonData):
        builder = cls()
        if not data["builder_type"] == cls.builder_type:
            raise
        values = data["value"]
        for value in values:
            text_type = value.get("type", "")
            matched = cls._get_matched_type(text_type)
            if not matched:
                continue
            builder.text_list.append(matched.parse(value))
        return builder


if __name__ == "__main__":
    builder = BlockTextBuilder()
    builder.text(value="hello ").mention(value="sandring ", user_id=2).text(
        value="this is rich text "
    ).hyperlink(value="Please visit Our Website ", url="https://google.com")
    json = builder.get_json()
    parsed_builder = BlockTextBuilder.parse_json(json)

    print(parsed_builder.get_json())
