from __future__ import annotations

import importlib.abc
import sys
import threading
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from typing_extensions import Self
else:

    class Self:
        def __repr__(self) -> str:
            return "<Placeholder for 'typing.Self'>"


class _LazyModule(ModuleType):
    """A subclass of the module type which triggers loading upon attribute access."""

    def __getattribute__(self, attr: str) -> Any:
        """Trigger the load of the module and return the attribute."""

        # All module metadata must be garnered from __spec__ in order to avoid using mutated values.
        __spec__: ModuleSpec = object.__getattribute__(self, "__spec__")

        loader_state = __spec__.loader_state
        with loader_state["lock"]:
            # Only the first thread to get the lock should trigger the load and reset the module's class.
            # The rest can now getattr().
            if object.__getattribute__(self, "__class__") is _LazyModule:
                # The first thread comes here multiple times as it descends the call stack.
                # The first time, it sets is_loading and triggers exec_module(), which will access module.__dict__,
                # module.__name__, and/or module.__spec__, reentering this method.
                # These accesses need to be allowed to proceed without triggering the load again.
                if loader_state["is_loading"] and attr.startswith("__") and attr.endswith("__"):
                    return object.__getattribute__(self, attr)
                loader_state["is_loading"] = True

                __dict__: dict[str, Any] = object.__getattribute__(self, "__dict__")

                # All module metadata must be gathered from __spec__ in order to avoid using mutated values.

                # Get the original name to make sure no object substitution occurred in sys.modules.
                original_name = __spec__.name

                # Figure out exactly what attributes were mutated between the creation of the module and now.
                attrs_then: dict[str, Any] = loader_state["__dict__"]
                attrs_now: dict[str, Any] = __dict__
                attrs_updated: dict[str, Any] = {}

                for key, value in attrs_now.items():
                    # Code that set an attribute may have kept a reference to the assigned object, making identity more
                    # important than equality.
                    if key not in attrs_then or id(attrs_now[key]) != id(attrs_then[key]):
                        attrs_updated[key] = value
                __spec__.loader.exec_module(self)  # pyright: ignore [reportOptionalMemberAccess]

                # If exec_module() was used directly there is no guarantee the module object was put into sys.modules.
                if original_name in sys.modules and id(self) != id(sys.modules[original_name]):
                    msg = f"module object for {original_name!r} substituted in sys.modules during a lazy load"
                    raise ValueError(msg)

                # Update after loading since that's what would happen in an eager loading situation.
                __dict__.update(attrs_updated)

                # Finally, stop triggering this method.
                self.__class__ = ModuleType  # pyright: ignore [reportIncompatibleMethodOverride]

        return getattr(self, attr)

    def __delattr__(self, attr: str) -> None:
        """Trigger the load and then perform the deletion."""

        # To trigger the load and raise an exception if the attribute doesn't exist.
        self.__getattribute__(attr)
        delattr(self, attr)


class LazyLoader(importlib.abc.Loader):
    """A loader that creates a module which defers loading until attribute access."""

    @staticmethod
    def __check_eager_loader(loader: type[importlib.abc.Loader] | importlib.abc.Loader) -> None:
        if not hasattr(loader, "exec_module"):
            msg = "loader must define exec_module()"
            raise TypeError(msg)

    def __init__(self, loader: importlib.abc.Loader) -> None:
        self.__check_eager_loader(loader)
        self.loader = loader

    @classmethod
    def factory(cls, loader: type[importlib.abc.Loader]) -> Callable[..., Self]:
        """Construct a callable which returns the eager loader made lazy."""

        cls.__check_eager_loader(loader)
        return lambda *args, **kwargs: cls(loader(*args, **kwargs))

    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        return self.loader.create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        """Make the module load lazily."""

        module.__spec__.loader = self.loader  # pyright: ignore [reportOptionalMemberAccess] # Let presence of None cause an exception.
        module.__loader__ = self.loader

        # Don't need to worry about deep-copying as trying to set an attribute on an object would have triggered the
        # load, e.g. ``module.__spec__.loader = None`` would trigger a load from trying to access module.__spec__.
        loader_state: dict[str, Any] = {
            "__dict__": module.__dict__.copy(),
            "__class__": module.__class__,
            "lock": threading.RLock(),
            "is_loading": False,
        }
        module.__spec__.loader_state = loader_state  # pyright: ignore [reportOptionalMemberAccess] # Let presence of None cause an exception.
        module.__class__ = _LazyModule
