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
    id: int
    username: str
    value: str
    type: Literal["mention"] = "mention"

    def json(self):
        return dict(
            value=self.value, type=self.type, id=self.id, username=self.username
        )


@dataclass
class Hidden(PlainText):
    value: str
    type: Literal["hidden"] = "hidden"


T = TypeVar("T", bound=PlainText)
P = ParamSpec("P")


class BlockTextBuilder:
    builder_type: Literal["block_text"] = "block_text"
    text_list: list[list[PlainText]]

    def __init__(self):
        self.text_list = []

    def push(self, block: PlainText):
        if self.text_list.__len__() == 0:
            self.text_list.append([])
        self.text_list[-1].append(block)

    def pop(self, supportIndex=-1):
        if self.text_list.__len__() == 0:
            raise
        return self.text_list.pop(supportIndex)

    def text_wrapper(self, kls: Callable[P, T]):
        def decorator(*args: P.args, **kwargs: P.kwargs) -> "BlockTextBuilder":
            text = kls(*args, **kwargs)
            self.push(text)
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

    def new_line(self):
        self.text_list.append([])
        return self

    def get_plain_text(self):
        lines = ""
        for num, line in enumerate(self.text_list):
            for block in line:
                lines += block.value
            lines += "\n"
        else:
            lines = lines.removesuffix("\n")
        return lines

    def get_json(self):
        lines: list[list[dict]] = []
        for line in self.text_list:
            blocks: list[dict] = []
            for block in line:
                if not block.value:
                    continue
                blocks.append(block.json())
            lines.append(blocks)
        return lines

    @classmethod
    def _get_matched_type(cls, text_type: str) -> type[Text] | None:
        texts: list[type[Text]] = [Text, Hyperlink, Mention, Hidden]  # type:ignore
        return next(filter(lambda x: x.type == text_type, texts), None)

    @classmethod
    def parse_json(cls, lines: list[list[dict]]):
        for line in lines:
            for block in line:
                text_type = block.get("type", "")
                matched = cls._get_matched_type(text_type)
                if not matched:
                    continue
                builder.push(matched.parse(block))
            builder.new_line()
        else:
            builder.pop(-1)
        return builder


if __name__ == "__main__":
    builder = BlockTextBuilder()
    builder.text(value="hello ").mention(
        value="@sandring ", id=2, username="sandring"
    ).text(value="this is rich text ").hyperlink(
        value="Please visit Our Website ", url="https://google.com"
    )
    json = builder.get_json()
    parsed_builder = BlockTextBuilder.parse_json(json)
