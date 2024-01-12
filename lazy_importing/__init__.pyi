from types import TracebackType

from typing_extensions import Self

__all__ = ("lazy_loading",)

class lazy_loading:
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
