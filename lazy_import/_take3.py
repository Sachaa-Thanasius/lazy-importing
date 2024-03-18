from __future__ import annotations

import sys
from collections.abc import Sequence
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self
else:

    class Self:
        pass


def _load_module(module: ModuleType) -> None:
    # Assumptions about spec state.
    assert module.__spec__
    assert module.__spec__.loader

    # All module metadata must be garnered from __spec__ in order to avoid using mutated values.

    # Stop triggering this method.
    module.__class__: ModuleType = module.__spec__.loader_state["__class__"]

    # Get the original name to make sure no object substitution occurred in sys.modules.
    original_name = module.__spec__.name

    # Figure out exactly what attributes were mutated between the creation of the module and now.
    attrs_then: dict[str, Any] = module.__spec__.loader_state["__dict__"]
    attrs_now = module.__dict__
    attrs_updated: dict[str, Any] = {}
    for key, value in attrs_now.items():
        # Code that set the attribute may have kept a reference to the assigned object,
        # making identity more important than equality.
        if key not in attrs_then or id(attrs_now[key]) != id(attrs_then[key]):
            attrs_updated[key] = value

    module.__spec__.loader.exec_module(module)

    # If exec_module() was used directly, there is no guarantee the module object was put into sys.modules.
    if original_name in sys.modules and id(module) != id(sys.modules[original_name]):
        msg = f"module object for {original_name!r} substituted in sys.modules during a lazy load"
        raise ValueError(msg)

    # Update after loading since that's what would happen in an eager loading situation.
    module.__dict__.update(attrs_updated)


class Placeholder:
    def __init__(self, placeholder_module: PlaceholderModule, actual_name: str):
        self.placeholder_module = placeholder_module
        self.actual_name = actual_name

    def __getattribute__(self, name: str):
        _load_module(self.placeholder_module)
        self = getattr(self.placeholder_module, self.actual_name)
        return getattr(self, name)

    def __setattr__(self, name: str, value: Any, /) -> None:
        self.__getattribute__(name)
        setattr(self, name, value)

    def __delattr__(self, name: str, /) -> None:
        self.__getattribute__(name)
        delattr(self, name)


class PlaceholderModule(ModuleType):
    def __getattribute__(self, name: str) -> Any:
        """Trigger the load of the module and return the attribute."""

        if getattr(self, "in_lazy_context", False):
            return Placeholder(self, name)

        _load_module(self)
        return getattr(self, name)

    def __delattr__(self, attr: str) -> None:
        """Trigger the load and then perform the deletion."""

        # To trigger the load and raise an exception if the attribute doesn't exist.
        self.__getattribute__(attr)
        delattr(self, attr)


class PlaceholderImporter(MetaPathFinder, Loader):
    def __init__(self) -> None:
        self.actual_loader: Loader | None = None

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: ModuleType | None = None,
        /,
    ) -> ModuleSpec | None:
        for finder in sys.meta_path:
            if finder is not self:
                spec = finder.find_spec(fullname, path, target)
                if spec is not None:
                    break
        else:
            msg = f"No module named {fullname!r}"
            raise ModuleNotFoundError(msg, name=fullname)

        self.actual_loader = spec.loader
        spec.loader = self
        return spec

    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        return self.actual_loader.create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        assert module.__spec__

        module.__spec__.loader = self.actual_loader
        module.__loader__ = self.actual_loader
        module.__spec__.loader_state = {
            "__dict__": module.__dict__.copy(),
            "__class__": module.__class__,
        }
        module.__class__ = PlaceholderModule


class lazy_import_v3:
    def __init__(self) -> None:
        self.importer = PlaceholderImporter()

    def __enter__(self) -> Self:
        sys.meta_path.insert(0, self.importer)
        return self

    def __exit__(self, *_: object) -> None:
        sys.meta_path.remove(self.importer)
