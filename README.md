# lazy-importing

An attempt at a context manager for conditional lazy imports in Python.

In this code is a simple import finder that delegates finding to the rest of the meta path, but upon finding the spec, substitutes the spec's loader with [`importlib.utils.LazyLoader`](https://docs.python.org/3.11/library/importlib.html#importlib.util.LazyLoader). The context manager temporarily places an instance of that finder at the front of the meta path, removing it upon exit.

This was made with the intention of providing a tool to prevent circular imports, an alternative to `if typing.TYPE_CHECKING` blocks, and a nice syntax for lazy imports that is understood by type-checkers. It doesn't manage it all yet, but that's the idea. Currently, it doesn't lazily load `from` imports that assign an actual class, function, etc. to the global namespace; that immediately triggers the module to load.

In practice, it looks something like this:

```py
from lazy_import import lazy_imp

with lazy_imp():
    import typing

# 'typing' isn't actually loaded until this stringified type annotation is
# evaluated, i.e. 'typing' is accessed in some other way.
# However, the type-checker will still understand it.
def example(data: "typing.Mapping[str, bool]") -> str:
    ...

# Until the annotation is evaluated or the module is used, the loading cost
# will never be payed.
typing.get_type_hints(example)
```
