from app.models.schemas import PaperEvidence, PaperMetadata
from app.services import datastet_service
from app.services.datastet_service import (
    extract_dataset_mentions_with_datastet_from_pdf,
    merge_extracted_dataset_names,
    normalize_datastet_mentions,
)
from app.services.paper_service import _enrich_evidence_with_datastet


def test_normalize_datastet_mentions_json():
    raw = {
        "mentions": [
            {"rawForm": "VLSP 2016", "context": "We use VLSP 2016."},
            {"rawForm": "AIVIVN 2019", "context": "and AIVIVN 2019."},
        ]
    }

    mentions = normalize_datastet_mentions(raw)

    names = [m["name"] for m in mentions]
    assert "VLSP 2016" in names
    assert "AIVIVN 2019" in names
    assert all(m["source"] == "datastet" for m in mentions)


def test_normalize_datastet_mentions_accepts_json_string():
    raw = '{"datasets": [{"name": "FLORES-200"}]}'

    mentions = normalize_datastet_mentions(raw)

    assert [m["name"] for m in mentions] == ["FLORES-200"]
    assert mentions[0]["source"] == "datastet"


def test_extract_from_pdf_returns_empty_on_failure(monkeypatch):
    # No cache hit.
    monkeypatch.setattr(
        datastet_service, "read_json_cache", lambda *a, **k: None
    )

    # Downloading the PDF fails.
    def raise_error(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(datastet_service, "download_pdf", raise_error)

    result = extract_dataset_mentions_with_datastet_from_pdf(
        "https://example.com/x.pdf"
    )

    assert result == []


def test_extract_from_pdf_returns_empty_on_post_failure(monkeypatch):
    monkeypatch.setattr(
        datastet_service, "read_json_cache", lambda *a, **k: None
    )
    monkeypatch.setattr(datastet_service, "download_pdf", lambda *a, **k: b"%PDF")

    def raise_error(*a, **k):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(
        "app.services.datastet_service.requests.post", raise_error
    )

    result = extract_dataset_mentions_with_datastet_from_pdf(
        "https://example.com/x.pdf"
    )

    assert result == []


def test_merge_extracted_dataset_names():
    existing = ["VLSP", "Vietnamese", "These"]
    datastet = ["VLSP 2016", "AIVIVN 2019"]

    merged = merge_extracted_dataset_names(existing, datastet)

    assert "VLSP 2016" in merged
    assert "AIVIVN 2019" in merged
    assert "Vietnamese" not in merged
    assert "These" not in merged
    assert "VLSP" not in merged


def test_paper_evidence_enrichment():
    paper = PaperMetadata(
        arxiv_id="1234.5678",
        title="A Paper",
        summary="An abstract.",
        url="https://arxiv.org/abs/1234.5678",
        pdf_url="https://arxiv.org/pdf/1234.5678",
    )
    evidence = PaperEvidence(
        paper_title=paper.title,
        paper_url=paper.url,
        evidence_sentence=(
            "We evaluate the proposed model on two datasets: "
            "VLSP 2016 and AIVIVN 2019."
        ),
        extracted_dataset_names=[],
        score=5,
        source_text_type="grobid_full_text",
    )
    mentions = [
        {
            "name": "VLSP 2016",
            "mention_text": "VLSP 2016",
            "context": "",
            "mention_type": "dataset",
            "section_title": None,
            "source": "datastet",
        },
        {
            "name": "AIVIVN 2019",
            "mention_text": "AIVIVN 2019",
            "context": "",
            "mention_type": "dataset",
            "section_title": None,
            "source": "datastet",
        },
    ]

    _enrich_evidence_with_datastet([evidence], mentions)

    assert "VLSP 2016" in evidence.extracted_dataset_names
    assert "AIVIVN 2019" in evidence.extracted_dataset_names
