"""A stub of a test file. TODO: Make more comprehensive."""

import importlib.util
import sys
import time

from lazy_import import lazy_imp, lazy_imp2, recipes


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
        import itertools
        import types
        import typing
        from importlib import abc

    assert concurrent.futures.as_completed
    print(f"Time taken for regular import = {ct.total_time}")


def test_recipe_docs():
    with catchtime() as ct:
        lazy_concurrent_futures = recipes.lazy_import_docs("concurrent.futures")
        lazy_contextlib = recipes.lazy_import_docs("contextlib")
        lazy_importlib_abc = recipes.lazy_import_docs("importlib.abc")
        lazy_inspect = recipes.lazy_import_docs("inspect")
        lazy_itertools = recipes.lazy_import_docs("itertools")
        lazy_types = recipes.lazy_import_docs("types")
        lazy_typing = recipes.lazy_import_docs("typing")

    assert lazy_concurrent_futures.as_completed
    print(f"Time taken for lazy import (based on importlib recipe) = {ct.total_time}")


def test_lazy_import_v1():
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
    print(f"Time taken for lazy import v1 = {ct.total_time}")


def test_lazy_import_v2():
    with catchtime() as ct:  # noqa: SIM117 # Display the separate block.
        with lazy_imp2():
            import concurrent.futures
            import contextlib
            import inspect
            import itertools
            import types
            import typing
            from importlib import abc

    assert concurrent.futures.as_completed
    print(f"Time taken for lazy import v2 = {ct.total_time}")
