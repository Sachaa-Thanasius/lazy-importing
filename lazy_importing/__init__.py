"""A way to lazy-load blocks of regular import statements.

What this package essentially does, in order:
    1. Recreates most of the behavior of importlib.__import__.
    2. Replaces the package loader at the very end of the __import__ process with importlib.utils.LazyLoader.
    3. Provides a context manager that temporarily monkeypatches builtins.__import__ with this lazy version.
"""
# Much of the code and docstrings below, excluding the lazy_loading class, is copied with a little modification from
# CPython's importlib.
# The full license is available at https://github.com/python/cpython/blob/3.11/LICENSE.

from __future__ import annotations

import builtins
import importlib.util
import sys
from importlib._bootstrap import _calc___package__, _handle_fromlist  # type: ignore

__all__ = ("lazy_loading",)


# Note: Functions imported from importlib._bootstrap might need to be reimplemented locally.


def _lazy_import_module(name: str, package: str | None = None):
    """An approximate implementation of import, but lazy.

    Mostly copied from the import recipe in the CPython importlib docs.
    """

    absolute_name = importlib.util.resolve_name(name, package)
    try:
        return sys.modules[absolute_name]
    except KeyError:
        pass

    path = None
    if "." in absolute_name:
        parent_name, _, child_name = absolute_name.rpartition(".")
        parent_module = _lazy_import_module(parent_name)
        path = parent_module.__spec__.submodule_search_locations

    for finder in sys.meta_path:
        spec = finder.find_spec(absolute_name, path)
        if spec is not None:
            break
    else:
        msg = f"No module named {absolute_name!r}"
        raise ModuleNotFoundError(msg, name=absolute_name)

    # Change the loader to be lazy. This is the only major "original" addition to all this.
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader

    module = importlib.util.module_from_spec(spec)
    sys.modules[absolute_name] = module
    spec.loader.exec_module(module)
    if path is not None:
        # If path exists, then the if block creating parent_module and child_name was executed.
        setattr(parent_module, child_name, module)  # type: ignore
    return module


def _new___import__(name: str, globals=None, locals=None, fromlist=(), level: int = 0):
    """The new version of __import__ that supports uses lazy module loading.

    Mostly copied from importlib.__import__.
    """

    package = None if level == 0 else _calc___package__(globals if globals is not None else {})
    module = _lazy_import_module(name, package)

    if not fromlist:
        # Return up to the first dot in 'name'. This is complicated by the fact that 'name' may be relative.
        if level == 0:
            return _lazy_import_module(name.partition(".")[0])
        if not name:
            return module

        # Figure out where to slice the module's name up to the first dot in 'name'.
        cut_off = len(name) - len(name.partition(".")[0])

        # Slice end needs to be positive to alleviate need to special-case when ``'.' not in name``.
        return sys.modules[module.__name__[: len(module.__name__) - cut_off]]
    if hasattr(module, "__path__"):
        return _handle_fromlist(module, fromlist, _lazy_import_module)
    return module


class lazy_loading:
    """A context manager that causes imports occuring within it to occur lazily."""

    def __enter__(self):
        self.old_import = builtins.__import__
        builtins.__import__ = _new___import__
        return self

    def __exit__(self, *_: object):
        builtins.__import__ = self.old_import
