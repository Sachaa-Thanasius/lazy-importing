import importlib.util
import sys
import time

from lazy_import import lazy_imp

from .recipes import lazy_import_docs

# TODO: Make tests more comprehensive.


class catchtime:
    """Utility for timing code execution."""

    def __enter__(self):
        self.total_time = time.perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self.total_time = time.perf_counter() - self.total_time


def test_regular_import():
    with catchtime() as ct:
        import concurrent.futures
        import contextlib
        import inspect
        import itertools
        import types
        import typing
        from importlib import abc

    assert concurrent.futures.as_completed
    print(f"Time taken for regular import = {ct.total_time}")


def test_recipe_docs():
    with catchtime() as ct:
        lazy_concurrent_futures = lazy_import_docs("concurrent.futures")
        lazy_contextlib = lazy_import_docs("contextlib")
        lazy_importlib_abc = lazy_import_docs("importlib.abc")
        lazy_inspect = lazy_import_docs("inspect")
        lazy_itertools = lazy_import_docs("itertools")
        lazy_types = lazy_import_docs("types")
        lazy_typing = lazy_import_docs("typing")

    assert lazy_concurrent_futures.as_completed
    print(f"Time taken for lazy import (based on importlib recipe) = {ct.total_time}")


def test_lazy_imp():
    with catchtime() as ct:  # noqa: SIM117 # Display the separate block.
        with lazy_imp():
            import concurrent.futures
            import contextlib
            import inspect
            import itertools
            import types
            import typing
            from importlib import abc

    assert concurrent.futures.as_completed
    print(f"Time taken for lazy import = {ct.total_time}")


def test_delayed_circular_import():
    import typing

    from tests.dummy_pkg import scratch1, scratch2

    assert typing.get_type_hints(scratch1.Scratch1.__init__) == {"scr": scratch2.Scratch2 | None}
    assert typing.get_type_hints(scratch2.Scratch2.__init__) == {"scr": scratch1.Scratch1 | None}

    if sys.version_info >= (3, 10):
        import inspect

        assert inspect.get_annotations(scratch1.Scratch1.__init__, eval_str=True) == {"scr": scratch2.Scratch2 | None}
        assert inspect.get_annotations(scratch2.Scratch2.__init__, eval_str=True) == {"scr": scratch1.Scratch1 | None}
