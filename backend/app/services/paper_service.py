from typing import List

from app.core.config import USE_DATASTET
from app.models.schemas import PaperEvidence, PaperMetadata
from app.services.datastet_service import (
    extract_dataset_mentions_with_datastet_from_pdf,
    merge_extracted_dataset_names,
)
from app.services.evidence_extractor import extract_evidence_from_text
from app.services.fulltext_service import download_pdf, extract_text_from_pdf_bytes
from app.services.grobid_service import extract_fulltext_sections


# Cap on how many DataStet-only evidence items we add per paper when the
# mention context cannot be matched to an existing evidence sentence.
_MAX_DATASTET_ONLY_ITEMS = 3

# Score used for DataStet-only evidence items so they are high enough to be
# displayed/matched without dominating strong rule-based evidence.
_DATASTET_EVIDENCE_SCORE = 4


def _enrich_evidence_with_datastet(
    evidence_items: List[PaperEvidence],
    datastet_mentions: List[dict],
) -> None:
    """Merge DataStet mention names into overlapping evidence sentences.

    A mention overlaps an evidence sentence when its name (or mention text)
    appears in the sentence (case-insensitive). Mutates evidence_items in place.
    """
    if not datastet_mentions:
        return

    for ev in evidence_items:
        sentence_low = (ev.evidence_sentence or "").lower()
        if not sentence_low:
            continue

        overlapping_names = [
            mention["name"]
            for mention in datastet_mentions
            if mention.get("name")
            and (
                mention["name"].lower() in sentence_low
                or (mention.get("mention_text") or "").lower() in sentence_low
            )
        ]

        if overlapping_names:
            ev.extracted_dataset_names = merge_extracted_dataset_names(
                ev.extracted_dataset_names, overlapping_names
            )


def _build_datastet_only_evidence(
    paper: PaperMetadata,
    datastet_mentions: List[dict],
    existing_items: List[PaperEvidence],
) -> List[PaperEvidence]:
    """Create a small number of DataStet-only evidence items.

    Only mentions that are not already represented in an existing evidence
    sentence are added, capped at _MAX_DATASTET_ONLY_ITEMS.
    """
    if not datastet_mentions:
        return []

    already_present: set[str] = set()
    for ev in existing_items:
        for name in ev.extracted_dataset_names or []:
            already_present.add(name.lower())

    new_items: List[PaperEvidence] = []
    for mention in datastet_mentions:
        name = (mention.get("name") or "").strip()
        if not name or name.lower() in already_present:
            continue

        sentence = mention.get("context") or mention.get("mention_text") or name

        new_items.append(
            PaperEvidence(
                paper_title=paper.title,
                paper_url=paper.url,
                evidence_sentence=sentence,
                extracted_dataset_names=[name],
                score=_DATASTET_EVIDENCE_SCORE,
                source_text_type="datastet",
                section_title=mention.get("section_title"),
            )
        )
        already_present.add(name.lower())

        if len(new_items) >= _MAX_DATASTET_ONLY_ITEMS:
            break

    return new_items


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

        # DataStet is tried first as the dataset-mention detector. It is fully
        # optional: any failure returns [] and the pipeline continues with the
        # existing GROBID/rule-based extraction below.
        datastet_mentions: List[dict] = []
        if USE_DATASTET:
            try:
                datastet_mentions = extract_dataset_mentions_with_datastet_from_pdf(
                    paper.pdf_url
                )
            except Exception:
                datastet_mentions = []

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

        # Enrich extracted dataset names using DataStet mentions where the
        # mention overlaps an evidence sentence, then add a few DataStet-only
        # items for mentions that could not be attached to a sentence.
        if datastet_mentions:
            _enrich_evidence_with_datastet(evidence_items, datastet_mentions)
            evidence_items.extend(
                _build_datastet_only_evidence(
                    paper=paper,
                    datastet_mentions=datastet_mentions,
                    existing_items=evidence_items,
                )
            )

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
