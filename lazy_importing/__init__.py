"""A way to lazy-load blocks of regular import statements."""

import importlib.abc
import importlib.util
import sys


class LazyFinder(importlib.abc.MetaPathFinder):
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


LAZY_FINDER = LazyFinder()


class lazy_loading:
    """A context manager that causes imports occuring within it to occur lazily."""

    def __enter__(self):
        sys.meta_path.insert(0, LAZY_FINDER)
        return self

    def __exit__(self, *_: object):
        sys.meta_path.remove(LAZY_FINDER)
