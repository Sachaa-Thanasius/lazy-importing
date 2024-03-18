from __future__ import annotations

import builtins
import sys
from collections.abc import Mapping, Sequence
from types import ModuleType

_template___getattr__ = """\
def __getattr__(name: str):
{if_stmts}
    msg = "module %r has no attribute %r" % (__name__, name)
    raise AttributeError(msg)
"""

_template_getattr_if_block = """\
    if name == {attr!r}:
        {import_stmt}
        print("Accessing {attr!r}")
        return {attr}
"""


class _PlaceholderModule(ModuleType):
    def __getattr__(self, name: str) -> None:
        return None


class lazy_imp2:
    def __init__(self) -> None:
        self._import_storage: dict[str, str] = {}

    def __enter__(self):
        if "__getattr__" in sys._getframe(1).f_globals:
            msg = "Will not replace existing module-level getattr."
            raise RuntimeError(msg)

        self._old_import = builtins.__import__
        builtins.__import__ = self._new___import__
        return self

    def __exit__(self, *_: object) -> None:
        builtins.__import__ = self._old_import
        mod_globals = sys._getframe(1).f_globals
        import_if_list: list[str] = []
        for attr, import_stmt in self._import_storage.items():
            # print(f"\n{attr} - {import_stmt}")
            # del mod_globals[attr]
            import_if_list.append(_template_getattr_if_block.format(attr=attr, import_stmt=import_stmt))

        import_if_block = "\n".join(import_if_list)
        exec(_template___getattr__.format(if_stmts=import_if_block), mod_globals)  # noqa: S102

    def _new___import__(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> _PlaceholderModule:
        if fromlist:
            for attr in fromlist:
                self._import_storage[attr] = f"from {'.' * level}{name} import {attr}"
            return _PlaceholderModule(name)

        mod_name, _, _ = name.partition(".")
        self._import_storage[mod_name] = f"import {'.' * level}{name}"
        return _PlaceholderModule(mod_name)
