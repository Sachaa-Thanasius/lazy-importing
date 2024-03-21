from lazy_import import lazy_imp

with lazy_imp():
    import tests.dummy_pkg.dummy2 as dummy2

__all__ = ("Dummy1",)


class Dummy1:
    def __init__(self, scr: "dummy2.Dummy2 | None"):
        self.scr = scr
