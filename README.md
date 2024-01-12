# lazy-importing

An attempt at a context manager for conditional lazy imports in Python.

The idea is that, using a context manager, one can temporarily replace `builtins.__import__`. That way, any regular imports (using `import x` syntax) occuring within the block of a context manager will use that modified `__import__` to find and load a module. In this case, I'm replacing `__import__` with something very similar; however, at the very last stage, before executing the imported module, this verison replaces the module's loader with `importlib.utils.LazyLoader`. That way, the import is technically deferred until later attribute access in the module.

This was made with the intention of providing a nice syntax for lazy imports so that they are understood by type-checkers.

In practice, it would look something like this:

```py
from lazy_importing import lazy_loading

with lazy_loading():
    import typing

# `typing` isn't actually fully imported until this stringified type annotation is evaluated.
# However, the type-checker will still understand it.
def example("typing.Mapping[str, bool]") -> str:
    ...

# Upon attribute access, *that's* when it'll get imported.
# If the annotation is never evaluated, the import cost is never payed.
typing.get_type_hints(example)
```
