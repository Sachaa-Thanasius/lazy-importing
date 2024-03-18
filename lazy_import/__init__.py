"""A way to lazy-load blocks of regular import statements."""

import importlib.abc
import importlib.util
import sys

__all__ = ("lazy_imp",)


class _LazyFinder(importlib.abc.MetaPathFinder):
    """A finder that delegates finding to the rest of the meta path and changes the found spec's loader.

    It currently wraps the actual loader with `importlib.util.LazyLoader`.
    """

    def find_spec(self, fullname: str, path, target=None, /):
        for finder in sys.meta_path:
            if finder != self:
                spec = finder.find_spec(fullname, path, target)
                if spec is not None:
                    break
        else:
            msg = f"No module named {fullname!r}"
            raise ModuleNotFoundError(msg, name=fullname)

        spec.loader = importlib.util.LazyLoader(spec.loader)  # pyright: ignore [reportArgumentType] # Let a None cause an exception naturally.
        return spec


_LAZY_FINDER = _LazyFinder()


class lazy_imp:
    """A context manager that causes imports occuring within it to occur lazily.

    Notes
    -----
    This isn't that clever. It adds a special finder to sys.meta_path and then removes it. That finder wraps the loaders
    for imported modules with importlib.util.LazyLoader. That's it.
    """

    def __enter__(self):
        if _LAZY_FINDER not in sys.meta_path:
            sys.meta_path.insert(0, _LAZY_FINDER)
        return self

    def __exit__(self, *_: object):
        sys.meta_path.remove(_LAZY_FINDER)
