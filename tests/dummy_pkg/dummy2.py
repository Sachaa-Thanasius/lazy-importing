from lazy_import import lazy_imp

with lazy_imp():
    import tests.dummy_pkg.dummy1 as dummy1

__all__ = ("Dummy2",)


class Dummy2:
    def __init__(self, scr: "dummy1.Dummy1 | None"):
        self.scr = scr
