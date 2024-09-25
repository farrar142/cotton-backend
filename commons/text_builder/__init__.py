from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Generic, Literal, ParamSpec, TypeVar, Union

from typing import Generic, ParamSpec, TypeVar, Callable


class PlainText:
    type: str
    value: str

    def json(self) -> dict[str, Any]:
        raise NotImplementedError


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
        return dict(value=self.value, type=self.type, user=self.user_id)


@dataclass
class Hidden(PlainText):
    value: str
    type: Literal["hidden"] = "hidden"


T = TypeVar("T", bound=PlainText)
P = ParamSpec("P")


class TextBuilder:
    text_list: list[PlainText]

    def __init__(self):
        self.text_list = []

    def text_wrapper(self, kls: Callable[P, T]):
        def decorator(*args: P.args, **kwargs: P.kwargs) -> "TextBuilder":
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
        return list(map(lambda text: text.json(), self.text_list))


if __name__ == "__main__":
    builder = TextBuilder()
    builder.text(value="hello ").mention(value="sandring ", user_id=2).text(
        value="this is rich text "
    ).hyperlink(value="Please visit Our Website ", url="https://google.com")
