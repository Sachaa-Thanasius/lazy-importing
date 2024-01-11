# ruff: noqa: PYI021 # Pyright recommends docstrings be included.

from collections.abc import Callable, Mapping, Sequence
from types import ModuleType, TracebackType
from typing import Any

from typing_extensions import Self

__all__ = ("lazy_loading",)

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

def _calc_package(globals: Mapping[str, Any]) -> str | None:
    """Calculate what __package__ should be.

    __package__ is not guaranteed to be defined or could be set to None
    to represent that its proper value is unknown.

    Copied from importlib._bootstrap._calc__package with minor changes.
    """

def _lazy_import_module(name: str, package: str | None = None) -> ModuleType:
    """An approximate implementation of import, but lazy.

    Mostly copied from importlib._bootstrap._calc__package.
    """

def _new_import(
    name: str,
    globals: Mapping[str, Any] | None = None,
    locals: Mapping[str, Any] | None = None,
    fromlist: Sequence[str] = (),
    level: int = 0,
) -> ModuleType:
    """The new version of __import__ that supports uses lazy module loading.

    Mostly copied from the import recipe in the CPython importlib docs.
    """

class lazy_loading:
    """A context manager that causes imports occuring within it to occur lazily."""
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
