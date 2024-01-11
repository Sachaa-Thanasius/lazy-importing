"""A stub of a test file. TODO: Expand."""

import time


class catchtime:
    def __enter__(self):
        self.total_time = time.perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self.total_time = time.perf_counter() - self.total_time


with catchtime() as ct:
    import lazy_importing

print(ct.total_time)
