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
from collections.abc import Callable, Mapping, Sequence
from importlib._bootstrap import _call_with_frames_removed  # type: ignore
from importlib.machinery import ModuleSpec
from types import ModuleType

__all__ = ("lazy_loading",)

_NEEDS_LOADING = object()


def _handle_fromlist(
    module: ModuleType,
    fromlist: Sequence[str],
    import_: Callable[[str], ModuleType],
    *,
    recursive: bool = False,
) -> ModuleType:
    """Figure out what __import__ should return.

    The import_ parameter is a callable which takes the name of module to
    import. It is required to decouple the function from assuming importlib's
    import implementation is desired.

    Mostly copied from importlib._bootstrap._handle_fromlist.
    """

    # The hell that is fromlist ...
    # If a package was imported, try to import stuff from fromlist.
    for x in fromlist:
        if not isinstance(x, str):  # type: ignore # Account for user input error?
            where = f"{module.__name__}.__all__" if recursive else "``from list''"
            msg = f"Item in {where} must be str, not {type(x).__name__}"
            raise TypeError(msg)
        if x == "*":
            if not recursive and hasattr(module, "__all__"):
                _handle_fromlist(module, module.__all__, import_, recursive=True)
        elif not hasattr(module, x):
            from_name = f"{module.__name__}.{x}"
            try:
                _call_with_frames_removed(import_, from_name)
            except ModuleNotFoundError as exc:
                # Backwards-compatibility dictates we ignore failed
                # imports triggered by fromlist for modules that don't
                # exist.
                if exc.name == from_name and sys.modules.get(from_name, _NEEDS_LOADING) is not None:
                    continue
                raise
    return module


def _calc_package(globals: Mapping[str, object]) -> str | None:
    """Calculate what __package__ should be.

    __package__ is not guaranteed to be defined or could be set to None
    to represent that its proper value is unknown.

    Mostly copied from importlib._bootstrap._calc__package.
    """

    import warnings

    package: str | None = globals.get("__package__")
    spec: ModuleSpec | None = globals.get("__spec__")
    if package is not None:
        if spec is not None and package != spec.parent:
            warnings.warn(
                f"__package__ != __spec__.parent ({package!r} != {spec.parent!r})",
                ImportWarning,
                stacklevel=3,
            )
        return package

    if spec is not None:
        return spec.parent

    warnings.warn(
        "can't resolve package from __spec__ or __package__, falling back on __name__ and __path__",
        ImportWarning,
        stacklevel=3,
    )
    package = globals["__name__"]  # type: ignore # Should exist as a string in most circumstances.
    if "__path__" not in globals:
        package = package.rpartition(".")[0]

    return package


def _lazy_import_module(name: str, package: str | None = None) -> ModuleType:
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

    # Change the loading to be lazy.
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader

    module = importlib.util.module_from_spec(spec)
    sys.modules[absolute_name] = module
    spec.loader.exec_module(module)
    if path is not None:
        # If path exists, then the if block creating parent_module and child_name was executed.
        setattr(parent_module, child_name, module)  # type: ignore
    return module


def _new_import(
    name: str,
    globals: Mapping[str, object] | None = None,
    locals: Mapping[str, object] | None = None,
    fromlist: Sequence[str] = (),
    level: int = 0,
) -> ModuleType:
    """The new version of __import__ that supports uses lazy module loading.

    Mostly copied from importlib.__import__.
    """

    package = None if level == 0 else _calc_package(globals or {})
    module = _lazy_import_module(name, package)

    if not fromlist:
        # Return up to the first dot in 'name'. This is complicated by the fact
        # that 'name' may be relative.
        if level == 0:
            return _lazy_import_module(name.partition(".")[0])
        if not name:
            return module

        # Figure out where to slice the module's name up to the first dot
        # in 'name'.
        cut_off = len(name) - len(name.partition(".")[0])
        # Slice end needs to be positive to alleviate need to special-case
        # when ``'.' not in name``.
        return sys.modules[module.__name__[: len(module.__name__) - cut_off]]
    if hasattr(module, "__path__"):
        return _handle_fromlist(module, fromlist, _lazy_import_module)
    return module


class lazy_loading:
    """A context manager that causes imports occuring within it to occur lazily."""

    def __enter__(self) -> lazy_loading:
        self.old_import = builtins.__import__
        builtins.__import__ = _new_import
        return self

    def __exit__(self, *_: object) -> None:
        builtins.__import__ = self.old_import
