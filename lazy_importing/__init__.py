"""A way to lazy-load blocks of regular import statements."""

import importlib.abc
import importlib.util
import sys


class _LazyFinder(importlib.abc.MetaPathFinder):
    """A finder that delegates finding to the rest of the meta path and changes the found spec's loader.

    Current loader it substitutes with is `importlib.util.LazyLoader`.
    """

    def find_spec(self, fullname: str, path, target=None, /):
        for finder in sys.meta_path[1:]:
            spec = finder.find_spec(fullname, path, target)
            if spec is not None:
                break
        else:
            msg = f"No module named {fullname!r}"
            raise ModuleNotFoundError(msg, name=fullname)

        spec.loader = importlib.util.LazyLoader(spec.loader)
        return spec


_LAZY_FINDER = _LazyFinder()


class lazy_loading:
    """A context manager that causes imports occuring within it to occur lazily."""

    def __enter__(self):
        if _LAZY_FINDER in sys.meta_path:
            msg = "Cannot use `with lazy_loading()` within another `with lazy_loading()` block."
            raise RuntimeError(msg)
        sys.meta_path.insert(0, _LAZY_FINDER)
        return self

    def __exit__(self, *_: object):
        sys.meta_path.remove(_LAZY_FINDER)
