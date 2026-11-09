import importlib


def test_package_imports() -> None:
    module = importlib.import_module("delta_cure")
    assert module.__name__ == "delta_cure"
