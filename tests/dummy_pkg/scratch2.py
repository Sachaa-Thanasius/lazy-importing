from lazy_import import lazy_imp

with lazy_imp():
    from . import scratch1

__all__ = ("Scratch2",)


class Scratch2:
    def __init__(self, scr: "scratch1.Scratch1 | None"):
        self.scr = scr
