from typing import Generic, ParamSpec, TypeVar, Callable

P = ParamSpec("P")
R = TypeVar("R")
P2 = ParamSpec("P2")
R2 = TypeVar("R2")


class Chain(Generic[R]):
    def __init__(self, value: R):
        self.value = value

    @property
    def c(self):
        return self.chain

    def chain(self, function: "Callable[[R],R2]"):
        return Chain(function(self.value))

    def __ror__(self, function: "Callable[[R],R2]"):
        return Chain(function(self.value))

    def __call__(self):
        return self.value


class ChainList(Generic[R]):
    def __init__(self, value: list[R]):
        self.value = value

    def map(self, function: Callable[[R, int, list[R]], R2]) -> "ChainList[R2]":
        mapped = list(
            map(lambda x: function(x[1], x[0], self.value), enumerate(self.value))
        )
        return ChainList(mapped)

    def filter(self, function: Callable[[R, int, list[R]], bool]) -> "ChainList[R]":
        filtered = list(
            filter(lambda x: function(x[1], x[0], self.value), enumerate(self.value))
        )
        mapped = ChainList(filtered).map(lambda x, i, t: x[1])
        return mapped


c = Chain
