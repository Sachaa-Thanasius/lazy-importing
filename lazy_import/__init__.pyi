import importlib.abc
import importlib.machinery
import types
from collections.abc import Sequence

from typing_extensions import Self

__all__ = ("lazy_imp",)

class _LazyFinder(importlib.abc.MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: types.ModuleType | None = None,
        /,
    ) -> importlib.machinery.ModuleSpec | None: ...

class lazy_imp:
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None: ...
