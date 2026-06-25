from typing import Dict, List, Set, Tuple

import re

from rapidfuzz import fuzz

from app.models.schemas import (
    DatasetCandidate,
    MatchedEvidence,
    MatchedPaperResult,
    PaperEvidence,
)
from app.services.alias_generator import normalize_text
from app.services.match_filter import (
    allow_fuzzy_for_alias,
    is_dataset_like_alias,
    is_valid_dataset_evidence,
)

_FUZZY_THRESHOLD = 90


def exact_alias_match(alias: str, sentence: str) -> bool:
    alias_norm = normalize_text(alias)
    sentence_norm = normalize_text(sentence)
    if not alias_norm or len(alias_norm) < 4:
        return False
    return bool(re.search(r"\b" + re.escape(alias_norm) + r"\b", sentence_norm))


def get_best_match(alias_list: List[str], sentence: str) -> tuple[str, str, float]:
    # Try exact match on all aliases first
    for alias in alias_list:
        if exact_alias_match(alias, sentence):
            if is_valid_dataset_evidence(sentence, alias, "exact_alias_match"):
                return alias, "exact_alias_match", 100.0

    # Fuzzy match only on aliases that explicitly permit it
    best_alias = ""
    best_score = 0.0

    for alias in alias_list:
        if not allow_fuzzy_for_alias(alias):
            continue
        alias_norm = normalize_text(alias)
        sentence_norm = normalize_text(sentence)
        if len(alias_norm) < 5:
            continue
        score = float(fuzz.partial_ratio(alias_norm, sentence_norm))
        if score > best_score:
            best_alias = alias
            best_score = score

    if best_score >= _FUZZY_THRESHOLD and is_valid_dataset_evidence(
        sentence, best_alias, "fuzzy_alias_match"
    ):
        return best_alias, "fuzzy_alias_match", best_score

    return "", "no_match", 0.0


def match_datasets_with_evidence(
    datasets: List[DatasetCandidate],
    evidence_items: List[PaperEvidence],
) -> List[MatchedPaperResult]:
    grouped_results: Dict[Tuple[str, str], MatchedPaperResult] = {}
    grouped_sentences: Dict[Tuple[str, str], Set[str]] = {}

    for dataset in datasets:
        raw_aliases = dataset.aliases or [dataset.name]
        aliases = [a for a in raw_aliases if is_dataset_like_alias(a)]
        if not aliases:
            continue

        for evidence in evidence_items:
            matched_alias, match_type, match_score = get_best_match(
                alias_list=aliases,
                sentence=evidence.evidence_sentence,
            )

            if match_type == "no_match":
                continue

            src_type = getattr(evidence, "source_text_type", "unknown") or "unknown"
            key = (dataset.name, evidence.paper_url)
            matched_evidence = MatchedEvidence(
                evidence_sentence=evidence.evidence_sentence,
                matched_alias=matched_alias,
                match_type=match_type,
                match_score=match_score,
                evidence_score=getattr(evidence, "score", 0) or 0,
                source_text_type=src_type,
            )

            if key not in grouped_results:
                grouped_results[key] = MatchedPaperResult(
                    dataset_name=dataset.name,
                    dataset_source=dataset.source,
                    dataset_url=dataset.url,
                    paper_title=evidence.paper_title,
                    paper_url=evidence.paper_url,
                    evidences=[matched_evidence],
                    best_match_score=match_score,
                    evidence_count=1,
                )
                grouped_sentences[key] = {evidence.evidence_sentence}
                continue

            if evidence.evidence_sentence in grouped_sentences[key]:
                continue

            grouped_results[key].evidences.append(matched_evidence)
            grouped_sentences[key].add(evidence.evidence_sentence)
            grouped_results[key].best_match_score = max(
                grouped_results[key].best_match_score,
                match_score,
            )
            grouped_results[key].evidence_count = len(grouped_results[key].evidences)

    matched_results = list(grouped_results.values())

    for item in matched_results:
        item.evidences.sort(
            key=lambda x: (x.match_score, x.evidence_score),
            reverse=True,
        )
        item.evidence_count = len(item.evidences)

    matched_results.sort(
        key=lambda x: (x.best_match_score, x.evidence_count),
        reverse=True,
    )

    return matched_results
