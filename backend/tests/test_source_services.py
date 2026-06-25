import builtins
import sys
import types

from app.services.elg_service import search_elg_resources
from app.services.openml_service import search_openml_datasets


def test_search_openml_returns_empty_list_when_openml_fails(monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("openml unavailable")

    monkeypatch.setattr(
        "app.services.openml_service.openml.datasets.list_datasets",
        raise_error,
    )

    results = search_openml_datasets(query="nlp", limit=5)

    assert results == []


def test_search_elg_returns_empty_list_when_elg_import_fails(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "elg":
            raise ImportError("elg not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    results = search_elg_resources(query="nlp", limit=5)

    assert results == []


def test_search_elg_returns_empty_list_when_catalog_search_fails(monkeypatch):
    class FailingCatalog:
        def __init__(self):
            pass

        def search(self, *args, **kwargs):
            raise RuntimeError("search failed")

    fake_elg_module = types.SimpleNamespace(Catalog=FailingCatalog)
    monkeypatch.setitem(sys.modules, "elg", fake_elg_module)

    results = search_elg_resources(query="nlp", limit=5)

    assert results == []
