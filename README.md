# lazy-importing

An attempt at a context manager for conditional lazy imports in Python.

In this code is a simple import finder that delegates finding to the rest of the meta path, but upon finding the spec, substitutes the spec's loader with [`importlib.utils.LazyLoader`](https://docs.python.org/3.11/library/importlib.html#importlib.util.LazyLoader). The context manager temporarily places an instance of that finder at the front of the meta path, removing it upon exit.

This was made with the intention of providing a tool to prevent circular imports, an alternative to `if typing.TYPE_CHECKING` blocks, and a nice syntax for lazy imports that is understood by type-checkers. It doesn't manage much of that well yet, but that's the idea. Currently, it doesn't support `from` imports that access an actual class, function, etc.; that immediately triggers the module to load.

In practice, it looks something like this:

```py
from lazy_importing import lazy_loading

with lazy_loading():
    import typing

# `typing` isn't actually fully imported until this stringified type annotation is evaluated, i.e. `typing` is accessed in some other way.
# However, the type-checker will still understand it.
def example(data: "typing.Mapping[str, bool]") -> str:
    ...

# If the annotation is never evaluated or the module is never used, the import cost is never payed.
typing.get_type_hints(example)
```
