import types

from app.services import hf_service
from app.services.hf_service import search_huggingface_datasets


def test_search_huggingface_parses_results(monkeypatch):
    fake_item = types.SimpleNamespace(
        id="org/cool-dataset",
        tags=["task:translation"],
        downloads=100,
        likes=5,
        description="A cool dataset.",
    )

    class FakeApi:
        def list_datasets(self, **kwargs):
            return [fake_item]

    monkeypatch.setattr(hf_service, "HfApi", lambda: FakeApi())

    results = search_huggingface_datasets("translation", limit=5)

    assert len(results) == 1
    candidate = results[0]
    assert candidate.name == "org/cool-dataset"
    assert candidate.source == "Hugging Face"
    assert candidate.url == "https://huggingface.co/datasets/org/cool-dataset"
    assert "downloads:100" in candidate.tags
    assert "likes:5" in candidate.tags


def test_search_huggingface_returns_empty_on_error(monkeypatch):
    class FailingApi:
        def list_datasets(self, **kwargs):
            raise RuntimeError("hub unavailable")

    monkeypatch.setattr(hf_service, "HfApi", lambda: FailingApi())

    assert search_huggingface_datasets("translation", limit=5) == []
