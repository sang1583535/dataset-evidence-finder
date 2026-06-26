from app.models.schemas import PaperMetadata
from app.services import paper_service
from app.services.paper_service import (
    extract_evidence_for_paper,
    extract_evidence_for_papers,
)


def _paper(title: str = "Our Method") -> PaperMetadata:
    return PaperMetadata(
        arxiv_id="1234.5678",
        title=title,
        summary="We evaluate our model on the SQuAD dataset.",
        url="https://arxiv.org/abs/1234.5678",
        pdf_url="https://arxiv.org/pdf/1234.5678",
    )


def test_extract_evidence_for_paper_abstract_only():
    evidence = extract_evidence_for_paper(_paper(), use_full_text=False)

    assert len(evidence) >= 1
    assert all(ev.source_text_type == "abstract" for ev in evidence)


def test_extract_evidence_for_paper_falls_back_when_download_fails(monkeypatch):
    def fail_download(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(paper_service, "download_pdf", fail_download)

    # Should not raise; still returns abstract evidence.
    evidence = extract_evidence_for_paper(_paper(), use_full_text=True)
    assert len(evidence) >= 1


def test_extract_evidence_for_papers_aggregates():
    papers = [_paper("Paper A"), _paper("Paper B")]
    evidence = extract_evidence_for_papers(papers, use_full_text=False)
    assert len(evidence) >= 2
