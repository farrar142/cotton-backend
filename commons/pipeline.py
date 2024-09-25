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


c = Chain
