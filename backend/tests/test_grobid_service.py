from app.services import grobid_service
from app.services.grobid_service import (
    GrobidSection,
    extract_fulltext_sections,
    is_grobid_available,
)


def test_is_grobid_available_true(monkeypatch):
    class FakeResponse:
        status_code = 200

    monkeypatch.setattr(
        "app.services.grobid_service.requests.get",
        lambda *a, **k: FakeResponse(),
    )

    assert is_grobid_available() is True


def test_is_grobid_available_false_on_error(monkeypatch):
    def raise_error(*a, **k):
        raise RuntimeError("connection refused")

    monkeypatch.setattr("app.services.grobid_service.requests.get", raise_error)

    assert is_grobid_available() is False


def test_extract_fulltext_sections_uses_cache(monkeypatch):
    cached = [{"title": "Experiments", "text": "We use SQuAD."}]
    monkeypatch.setattr(grobid_service, "read_json_cache", lambda *a, **k: cached)

    def fail_post(*a, **k):
        raise AssertionError("should not call GROBID when cache hit")

    monkeypatch.setattr("app.services.grobid_service.requests.post", fail_post)

    sections = extract_fulltext_sections("https://example.com/x.pdf", b"%PDF")

    assert sections == [GrobidSection(title="Experiments", text="We use SQuAD.")]
