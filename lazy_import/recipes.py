import importlib
import importlib.util
import sys
import types
from typing import Any, Callable, Iterable, Tuple


class ModuleAttributeError(AttributeError):
    def __init__(self, module_name: str, attr_name: str) -> None:
        super().__init__(f"module {module_name!r} has no attribute {attr_name!r}")


def lazy_import_docs(name: str) -> types.ModuleType:
    """Lazy import recipe from the importlib docs.

    Source: https://docs.python.org/3.11/library/importlib.html#implementing-lazy-imports
    """

    spec = importlib.util.find_spec(name)
    # Let presence of None cause an exception.
    loader = importlib.util.LazyLoader(spec.loader)  # type: ignore
    spec.loader = loader  # type: ignore
    module = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def lazy_import_brett(importer_name: str, to_import: Iterable[str]) -> Tuple[types.ModuleType, Callable[[str], Any]]:
    """Lazy import recipe from Brett Cannon's modutils package.

    Source: https://snarky.ca/lazy-importing-in-python-3-7/

    Return the importing module and a callable for lazy importing.

    The module named by importer_name represents the module performing the
    import to help facilitate resolving relative imports.

    to_import is an iterable of the modules to be potentially imported (absolute
    or relative). The `as` form of importing is also supported,
    e.g. `pkg.mod as spam`.

    This function returns a tuple of two items. The first is the importer
    module for easy reference within itself. The second item is a callable to be
    set to `__getattr__`.
    """

    module = importlib.import_module(importer_name)
    import_mapping: dict[str, str] = {}
    for name in to_import:
        importing, _, binding = name.partition(" as ")
        if not binding:
            _, _, binding = importing.rpartition(".")
        import_mapping[binding] = importing

    def __getattr__(name: str, /) -> Any:
        if name not in import_mapping:
            raise ModuleAttributeError(importer_name, name)
        importing = import_mapping[name]
        # imortlib.import_module() implicitly sets submodules on this module as appropriate for direct imports.
        imported = importlib.import_module(importing, module.__spec__.parent)  # type: ignore # # Let presence of None cause an exception.
        setattr(module, name, imported)
        return imported

    return module, __getattr__
