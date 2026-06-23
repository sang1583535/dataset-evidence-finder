from typing import List

from rapidfuzz import fuzz

from app.models.schemas import DatasetCandidate, PaperEvidence, MatchedResult
from app.services.alias_generator import normalize_text


def exact_alias_match(alias: str, sentence: str) -> bool:
    alias_norm = normalize_text(alias)
    sentence_norm = normalize_text(sentence)

    if not alias_norm:
        return False

    # Avoid matching very short aliases like "qa", "as", "en"
    if len(alias_norm) < 4:
        return False

    return alias_norm in sentence_norm


def fuzzy_alias_match(alias: str, sentence: str, threshold: int = 90) -> bool:
    alias_norm = normalize_text(alias)
    sentence_norm = normalize_text(sentence)

    if not alias_norm:
        return False

    if len(alias_norm) < 5:
        return False

    score = fuzz.partial_ratio(alias_norm, sentence_norm)

    return score >= threshold


def get_best_match(alias_list: List[str], sentence: str) -> tuple[str, str, float]:
    best_alias = ""
    best_type = "no_match"
    best_score = 0.0

    for alias in alias_list:
        if exact_alias_match(alias, sentence):
            return alias, "exact_alias_match", 100.0

        alias_norm = normalize_text(alias)
        sentence_norm = normalize_text(sentence)

        if len(alias_norm) >= 5:
            score = fuzz.partial_ratio(alias_norm, sentence_norm)

            if score > best_score:
                best_alias = alias
                best_type = "fuzzy_alias_match"
                best_score = float(score)

    if best_score >= 90:
        return best_alias, best_type, best_score

    return "", "no_match", 0.0


def match_datasets_with_evidence(
    datasets: List[DatasetCandidate],
    evidence_items: List[PaperEvidence],
) -> List[MatchedResult]:
    matched_results = []

    for dataset in datasets:
        aliases = dataset.aliases or [dataset.name]

        for evidence in evidence_items:
            matched_alias, match_type, match_score = get_best_match(
                alias_list=aliases,
                sentence=evidence.evidence_sentence,
            )

            if match_type == "no_match":
                continue

            matched_results.append(
                MatchedResult(
                    dataset_name=dataset.name,
                    matched_alias=matched_alias,
                    dataset_source=dataset.source,
                    dataset_url=dataset.url,
                    paper_title=evidence.paper_title,
                    paper_url=evidence.paper_url,
                    evidence_sentence=evidence.evidence_sentence,
                    match_type=match_type,
                    match_score=match_score,
                )
            )

    # Highest confidence first
    matched_results.sort(key=lambda x: x.match_score, reverse=True)

    return matched_results