from lazy_import.recipes import lazy_import_brett

mod, __getattr__ = lazy_import_brett(__name__, {".scratch as thingy"})


def test2():
    return mod.thingy.Example


print(test2())
print(mod)
