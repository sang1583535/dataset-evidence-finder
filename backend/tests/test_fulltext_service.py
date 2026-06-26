import fitz

from app.services import fulltext_service
from app.services.fulltext_service import (
    download_pdf,
    extract_text_from_pdf_bytes,
    get_pdf_text,
)


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_download_pdf_returns_content(monkeypatch):
    class FakeResponse:
        content = b"%PDF-fake"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        "app.services.fulltext_service.requests.get",
        lambda *a, **k: FakeResponse(),
    )

    assert download_pdf("https://example.com/x.pdf") == b"%PDF-fake"


def test_extract_text_from_pdf_bytes():
    pdf_bytes = _make_pdf_bytes("Hello dataset world")
    text = extract_text_from_pdf_bytes(pdf_bytes)
    assert "Hello dataset world" in text


def test_get_pdf_text_uses_cache(monkeypatch):
    monkeypatch.setattr(
        fulltext_service, "read_json_cache", lambda *a, **k: "cached text"
    )

    def fail_download(*a, **k):
        raise AssertionError("should not download when cache hit")

    monkeypatch.setattr(fulltext_service, "download_pdf", fail_download)

    assert get_pdf_text("https://example.com/x.pdf") == "cached text"
