"""Second-pass dataset search.

Rule-based extraction of dataset-like names from GROBID paper evidence,
followed by a small, cached lookup against dataset sources only.

No ML models are used. The second pass never searches arXiv again.
"""

import re
from typing import List, Optional

from app.models.schemas import DatasetCandidate, PaperEvidence
from app.services.alias_generator import normalize_text
from app.services.cache_service import (
    make_cache_key,
    read_json_cache,
    write_json_cache,
)


_SECOND_PASS_TTL = 24 * 60 * 60  # 24 hours


_USEFUL_SECTION_TERMS = [
    "dataset",
    "datasets",
    "data",
    "corpus",
    "corpora",
    "benchmark",
    "benchmarks",
    "experimental setup",
    "experiments",
    "evaluation",
    "results",
    "results and discussion",
    "training data",
    "test data",
]


_COMMON_SINGLE_WORDS = {
    "vietnamese",
    "english",
    "these",
    "this",
    "experimental",
    "results",
}


_GENERIC_TASK_PHRASES = {
    "sentiment analysis",
    "machine translation",
    "natural language processing",
}


_GENERIC_WORDS = {
    "dataset",
    "corpus",
    "benchmark",
    "model",
    "system",
    "method",
    "e-commerce",
}


# Regex patterns for dataset-like names.
_ACRONYM_YEAR = re.compile(r"\b[A-Z]{2,}\s+\d{4}\b")
_ACRONYM_OPT_YEAR = re.compile(r"\b[A-Z]{2,}(?:[- ]?\d{2,4})?\b")
_HYPHEN_DIGIT = re.compile(r"\b[A-Za-z]+(?:[-_][A-Za-z0-9]+)+\b")


def is_useful_evidence_section(section_title: Optional[str]) -> bool:
    """Return True if the section is likely to mention datasets."""
    if not section_title:
        return False

    section_norm = normalize_text(section_title)
    if not section_norm:
        return False

    for term in _USEFUL_SECTION_TERMS:
        term_norm = normalize_text(term)
        if term_norm and term_norm in section_norm:
            return True

    return False


def is_valid_second_pass_query(name: str) -> bool:
    """Filter noisy candidate names before using them as dataset queries."""
    if not name:
        return False

    stripped = name.strip()
    if len(stripped) < 3:
        return False

    words = stripped.split()
    if len(words) > 6:
        return False

    low = stripped.lower()
    norm = normalize_text(stripped)

    if low in _COMMON_SINGLE_WORDS or norm in {
        normalize_text(w) for w in _COMMON_SINGLE_WORDS
    }:
        return False

    if low in _GENERIC_WORDS or norm in {
        normalize_text(w) for w in _GENERIC_WORDS
    }:
        return False

    if norm in {normalize_text(p) for p in _GENERIC_TASK_PHRASES}:
        return False

    return True


def _regex_extract_names(sentence: str) -> List[str]:
    """Extract dataset-like names from a sentence using regex patterns.

    Longer, more specific forms are returned first so that downstream
    deduplication can prefer them over short acronyms.
    """
    if not sentence:
        return []

    names: List[str] = []
    seen: set[str] = set()

    for pattern in (_ACRONYM_YEAR, _HYPHEN_DIGIT, _ACRONYM_OPT_YEAR):
        for match in pattern.findall(sentence):
            candidate = match.strip()
            norm = normalize_text(candidate)
            if candidate and norm and norm not in seen:
                seen.add(norm)
                names.append(candidate)

    return names


def _is_extension_of(longer_norm: str, shorter_norm: str) -> bool:
    """Return True if longer_norm is shorter_norm plus extra trailing tokens."""
    long_tokens = longer_norm.split()
    short_tokens = shorter_norm.split()

    if len(long_tokens) <= len(short_tokens):
        return False

    return long_tokens[: len(short_tokens)] == short_tokens


def _merge_prefer_longer(ordered_names: List[str]) -> List[str]:
    """Deduplicate names, preferring longer specific forms.

    E.g. prefer "VLSP 2016" over "VLSP" and "AIVIVN 2019" over "AIVIVN".
    Input order is preserved as the primary priority.
    """
    selected: List[str] = []

    for name in ordered_names:
        norm = normalize_text(name)
        if not norm:
            continue

        skip = False
        replace_idx: Optional[int] = None

        for i, sel in enumerate(selected):
            sel_norm = normalize_text(sel)
            if norm == sel_norm:
                skip = True
                break
            if _is_extension_of(norm, sel_norm):
                replace_idx = i
                break
            if _is_extension_of(sel_norm, norm):
                skip = True
                break

        if skip:
            continue

        if replace_idx is not None:
            selected[replace_idx] = name
        else:
            selected.append(name)

    return selected


def extract_second_pass_queries_from_evidence(
    evidence_items: List[PaperEvidence],
    max_queries: int = 3,
) -> List[str]:
    """Extract a small number of dataset-like queries from paper evidence.

    Priority tiers (highest first):
      0. grobid_full_text + useful section + score >= 4
      1. grobid_full_text + useful section
      2. everything else (e.g. abstract evidence)
    """
    tiers: dict[int, List[str]] = {0: [], 1: [], 2: []}

    for ev in evidence_items or []:
        is_full = ev.source_text_type == "grobid_full_text"
        useful = is_useful_evidence_section(ev.section_title)
        score = ev.score or 0

        if is_full and useful and score >= 4:
            tier = 0
        elif is_full and useful:
            tier = 1
        else:
            tier = 2

        candidate_names: List[str] = []
        candidate_names.extend(ev.extracted_dataset_names or [])
        candidate_names.extend(_regex_extract_names(ev.evidence_sentence or ""))

        for name in candidate_names:
            if is_valid_second_pass_query(name):
                tiers[tier].append(name)

    ordered: List[str] = tiers[0] + tiers[1] + tiers[2]
    merged = _merge_prefer_longer(ordered)

    return merged[:max_queries]


def deduplicate_dataset_candidates(
    candidates: List[DatasetCandidate],
) -> List[DatasetCandidate]:
    """Deduplicate by normalized name, source and url. Keep the first."""
    seen: set[tuple[str, str, str]] = set()
    result: List[DatasetCandidate] = []

    for candidate in candidates or []:
        key = (
            normalize_text(candidate.name or ""),
            candidate.source or "",
            candidate.url or "",
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate)

    return result


def _cached_source_search(
    namespace: str,
    search_fn,
    query: str,
    limit: int,
) -> List[DatasetCandidate]:
    """Run a source search with a 24h JSON cache. Failures never crash."""
    key = make_cache_key(query, str(limit))

    cached = read_json_cache(namespace, key, ttl_seconds=_SECOND_PASS_TTL)
    if cached is not None:
        try:
            return [DatasetCandidate(**item) for item in cached]
        except Exception:
            pass

    try:
        results = search_fn(query=query, limit=limit)
    except Exception:
        return []

    try:
        write_json_cache(namespace, key, [c.model_dump() for c in results])
    except Exception:
        pass

    return results


def second_pass_dataset_lookup(
    queries: List[str],
    use_elg: bool,
    use_openml: bool,
    use_datacite: bool,
    max_results_per_source: int = 2,
) -> List[DatasetCandidate]:
    """Search dataset sources only using the extracted queries.

    Hugging Face is always searched. ELG, OpenML and DataCite are searched
    only when enabled. Each source is limited and wrapped defensively so a
    single failing source does not stop the others.
    """
    # Imported lazily and conditionally so pure extraction logic does not
    # require optional heavy dependencies (e.g. openml) at import time, and
    # disabled sources are never imported.
    from app.services.hf_service import search_huggingface_datasets

    sources = [("hf_search", search_huggingface_datasets)]
    if use_elg:
        from app.services.elg_service import search_elg_resources

        sources.append(("elg_search", search_elg_resources))
    if use_openml:
        from app.services.openml_service import search_openml_datasets

        sources.append(("openml_search", search_openml_datasets))
    if use_datacite:
        from app.services.datacite_service import search_datacite_datasets

        sources.append(("datacite_search", search_datacite_datasets))

    collected: List[DatasetCandidate] = []

    for query in queries or []:
        for namespace, search_fn in sources:
            results = _cached_source_search(
                namespace=namespace,
                search_fn=search_fn,
                query=query,
                limit=max_results_per_source,
            )

            for candidate in results[:max_results_per_source]:
                tags = list(candidate.tags or [])
                if "second-pass" not in tags:
                    tags.append("second-pass")
                tags.append(f"query:{query}")
                candidate.tags = tags

                # Add the originating query as an alias. The query was
                # extracted directly from paper evidence, so it matches the
                # evidence wording even when the source's own name/aliases
                # use a different format (e.g. HF "owner/VLSP2016" vs the
                # evidence form "VLSP 2016").
                aliases = list(candidate.aliases or [])
                if query not in aliases:
                    aliases.append(query)
                candidate.aliases = aliases

                collected.append(candidate)

    return deduplicate_dataset_candidates(collected)
