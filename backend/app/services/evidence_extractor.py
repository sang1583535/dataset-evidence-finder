import re
from typing import List

from app.core.config import EVIDENCE_TERMS
from app.models.schemas import PaperEvidence, PaperMetadata


DATASET_NAME_PATTERNS = [
    r"\b[A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+)*\b",
    r"\b[A-Za-z]+-[A-Za-z0-9\-]+\b",
    r"\b[A-Z]{2,}[A-Za-z0-9\-]*\b",
    r"\b[A-Za-z0-9]+/[A-Za-z0-9\-_]+\b",
]

STOPWORDS = {
    "We",
    "This",
    "The",
    "Our",
    "Table",
    "Figure",
    "Section",
    "English",
    "Data",
    "Dataset",
    "Datasets",
    "Corpus",
    "Experiments",
    "Evaluation",
    "Results",
}


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    text = clean_text(text)
    return re.split(r"(?<=[.!?])\s+", text)


def contains_evidence_term(sentence: str) -> bool:
    lower_sentence = sentence.lower()
    return any(term in lower_sentence for term in EVIDENCE_TERMS)


def score_evidence_sentence(sentence: str) -> int:
    lower = sentence.lower()
    score = 0

    strong_terms = [
        "dataset",
        "datasets",
        "benchmark",
        "corpus",
        "corpora",
    ]

    usage_terms = [
        "we use",
        "we used",
        "we evaluate",
        "we evaluated",
        "trained on",
        "fine-tuned on",
        "experiments on",
        "evaluate on",
        "evaluation on",
    ]

    section_terms = [
        "experimental setup",
        "experiments",
        "evaluation",
        "results",
        "data",
    ]

    if any(term in lower for term in strong_terms):
        score += 3

    if any(term in lower for term in usage_terms):
        score += 3

    if any(term in lower for term in section_terms):
        score += 1

    if len(sentence.split()) < 6:
        score -= 2

    if len(sentence.split()) > 80:
        score -= 1

    return score


def extract_dataset_like_names(sentence: str) -> List[str]:
    names = set()

    for pattern in DATASET_NAME_PATTERNS:
        for match in re.findall(pattern, sentence):
            match = match.strip()

            if len(match) <= 2:
                continue

            if match in STOPWORDS:
                continue

            names.add(match)

    return sorted(names)


def extract_evidence_from_text(
    paper: PaperMetadata,
    text: str,
    source_text_type: str,
    max_sentences: int = 8,
) -> List[PaperEvidence]:
    evidence_items = []

    for sentence in split_sentences(text):
        if not contains_evidence_term(sentence):
            continue

        score = score_evidence_sentence(sentence)

        if score <= 0:
            continue

        evidence_items.append(
            PaperEvidence(
                paper_title=paper.title,
                paper_url=paper.url,
                evidence_sentence=sentence,
                extracted_dataset_names=extract_dataset_like_names(sentence),
                score=score,
                source_text_type=source_text_type,
            )
        )

    evidence_items.sort(key=lambda x: x.score, reverse=True)

    return evidence_items[:max_sentences]