from typing import List

from app.models.schemas import PaperMetadata, PaperEvidence
from app.services.evidence_extractor import extract_evidence_from_text
from app.services.fulltext_service import get_pdf_text


def extract_evidence_for_paper(
    paper: PaperMetadata,
    use_full_text: bool = True,
) -> List[PaperEvidence]:
    evidence_items = []

    # Always use title + abstract first
    abstract_text = f"{paper.title}. {paper.summary}"
    evidence_items.extend(
        extract_evidence_from_text(
            paper=paper,
            text=abstract_text,
            source_text_type="abstract",
            max_sentences=5,
        )
    )

    # Then optionally use PDF full text
    if use_full_text:
        try:
            full_text = get_pdf_text(paper.pdf_url, max_pages=12)
            evidence_items.extend(
                extract_evidence_from_text(
                    paper=paper,
                    text=full_text,
                    source_text_type="full_text_pdf",
                    max_sentences=8,
                )
            )
        except Exception:
            # Do not crash the whole search if one PDF fails
            pass

    # Remove duplicate sentences
    unique = []
    seen = set()

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
    all_evidence = []

    for paper in papers:
        all_evidence.extend(
            extract_evidence_for_paper(
                paper=paper,
                use_full_text=use_full_text,
            )
        )

    return all_evidence