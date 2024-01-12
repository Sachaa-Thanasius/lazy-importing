"""A stub of a test file. TODO: Make more comprehensive."""

import importlib.util
import sys
import time


def lazy_import(name: str):
    """Lazy import recipe from the importlib docs.

    Source: https://docs.python.org/3.11/library/importlib.html#implementing-lazy-imports
    """

    spec = importlib.util.find_spec(name)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class catchtime:
    """Utility for timing code execution."""

    def __enter__(self):
        self.total_time = time.perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self.total_time = time.perf_counter() - self.total_time


def test_lazy_import_recipe():
    with catchtime() as ct:
        lazy_concurrent_futures = lazy_import("concurrent.futures")
        lazy_typing = lazy_import("typing")
        lazy_types = lazy_import("types")
        lazy_contextlib = lazy_import("contextlib")
        lazy_itertools = lazy_import("itertools")

    print(f"Time taken for lazy import (based on importlib recipe) = {ct.total_time}")


def test_lazy_import_custom():
    import lazy_importing

    with catchtime() as ct:
        with lazy_importing.lazy_loading():
            import concurrent.futures
            import contextlib
            import itertools
            import types
            import typing

    print(f"Time taken for lazy import = {ct.total_time}")


def test_regular_import():
    with catchtime() as ct:
        import concurrent.futures
        import contextlib
        import itertools
        import types
        import typing

    print(f"Time taken for regular import = {ct.total_time}")


def run_test():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "import_type",
        help="The type of import to test the speed of.",
        choices=["regular", "lazy", "lazy-recipe"],
    )
    args = parser.parse_args()
    if args.import_type == "regular":
        test_regular_import()
    elif args.import_type == "lazy":
        test_lazy_import_custom()
    elif args.import_type == "lazy-recipe":
        test_lazy_import_recipe()


if __name__ == "__main__":
    raise SystemExit(run_test())
