from typing import List

from app.models.schemas import PaperEvidence, PaperMetadata
from app.services.evidence_extractor import extract_evidence_from_text
from app.services.fulltext_service import download_pdf, extract_text_from_pdf_bytes
from app.services.grobid_service import extract_fulltext_sections


def extract_evidence_for_paper(
    paper: PaperMetadata,
    use_full_text: bool = True,
) -> List[PaperEvidence]:
    evidence_items: List[PaperEvidence] = []

    # Always extract from title + abstract
    abstract_text = f"{paper.title}. {paper.summary}"
    evidence_items.extend(
        extract_evidence_from_text(
            paper=paper,
            text=abstract_text,
            source_text_type="abstract",
            max_sentences=5,
        )
    )

    if use_full_text:
        pdf_bytes = None
        grobid_ok = False

        # Download PDF once; reused by both GROBID and PyMuPDF fallback
        try:
            pdf_bytes = download_pdf(paper.pdf_url)
        except Exception:
            pass

        if pdf_bytes is not None:
            # Try GROBID first
            try:
                sections = extract_fulltext_sections(paper.pdf_url, pdf_bytes)
                if sections:
                    grobid_ok = True
                    for section in sections:
                        section_evs = extract_evidence_from_text(
                            paper=paper,
                            text=section.text,
                            source_text_type="grobid_full_text",
                            max_sentences=4,
                        )
                        for ev in section_evs:
                            ev.section_title = section.title
                        evidence_items.extend(section_evs)
            except Exception:
                pass

            # Fallback to PyMuPDF using the already-downloaded bytes
            if not grobid_ok:
                try:
                    full_text = extract_text_from_pdf_bytes(pdf_bytes, max_pages=12)
                    evidence_items.extend(
                        extract_evidence_from_text(
                            paper=paper,
                            text=full_text,
                            source_text_type="full_text_pdf",
                            max_sentences=8,
                        )
                    )
                except Exception:
                    pass

    # Deduplicate and rank
    unique: List[PaperEvidence] = []
    seen: set[str] = set()
    for item in evidence_items:
        key = item.evidence_sentence.lower().strip()
        if key not in seen:
            unique.append(item)
            seen.add(key)

    unique.sort(key=lambda x: x.score, reverse=True)
    return unique[:10]


def extract_evidence_for_papers(
    papers: List[PaperMetadata],
    use_full_text: bool = True,
) -> List[PaperEvidence]:
    all_evidence: List[PaperEvidence] = []
    for paper in papers:
        all_evidence.extend(
            extract_evidence_for_paper(paper=paper, use_full_text=use_full_text)
        )
    return all_evidence
