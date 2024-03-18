from lazy_import import lazy_imp

with lazy_imp():
    from tests.dummy_pkg import scratch2

__all__ = ("Scratch1",)


class Scratch1:
    def __init__(self, scr: "scratch2.Scratch2 | None"):
        self.scr = scr
