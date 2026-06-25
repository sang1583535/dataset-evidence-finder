import re
from typing import Optional

from app.models.schemas import DatasetCandidate


_GENERIC_TERMS = {
    "dataset", "corpus", "data", "text", "nlp", "language",
    "classification", "translation", "speech", "benchmark",
    "training", "evaluation", "train", "test", "dev",
    "validation", "model", "task",
}

_SEARCH_STOPWORDS = {
    "a", "an", "the", "for", "of", "in", "on", "by", "at", "to",
    "and", "or", "is", "are", "was", "be", "has", "had", "with",
    "from", "that", "this", "as", "its", "it", "using", "via",
    "based", "approach", "intensity", "analysis", "some", "new",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def is_good_alias(alias: str) -> bool:
    if not alias or not alias.strip():
        return False

    norm = _normalize(alias)

    if len(norm) < 4:
        return False

    words = norm.split()

    if len(words) > 6:
        return False

    if all(w in _GENERIC_TERMS for w in words):
        return False

    return True


def _short_name(name: str) -> str:
    if "/" in name:
        return name.split("/")[-1]
    if ":" in name:
        prefix = name.split(":", 1)[0].strip()
        if prefix and " " not in prefix:
            return prefix
    return name


def _description_keywords(name: str, max_words: int = 4) -> list[str]:
    """Extract meaningful search terms from the description part of a colon-style name."""
    if ":" not in name:
        return []
    desc = name.split(":", 1)[1].strip()
    words = re.sub(r"[^a-zA-Z0-9]", " ", desc).split()
    return [
        w for w in words
        if len(w) > 2 and w.lower() not in _SEARCH_STOPWORDS
    ][:max_words]


def choose_best_alias(candidate: DatasetCandidate) -> Optional[str]:
    short = _short_name(candidate.name)
    if is_good_alias(short):
        return short

    if is_good_alias(candidate.name):
        return candidate.name

    good = [a for a in candidate.aliases if is_good_alias(a)]
    if not good:
        return None

    good.sort(key=lambda a: (len(_normalize(a).split()), len(a)))
    return good[0]


def _choose_arXiv_query(candidate: DatasetCandidate) -> Optional[str]:
    """Return the best arXiv search query for this candidate.

    For colon-style ELG names, the short prefix (e.g. 'VnEmoLex') may not be
    indexed by arXiv. Use description keywords instead so that the paper can
    be found via title/abstract term matching.
    """
    name = candidate.name

    # Colon-style: "ShortId: long descriptive title" — use description keywords
    if ":" in name and "/" not in name:
        keywords = _description_keywords(name)
        if len(keywords) >= 2:
            return " ".join(keywords)
        # Fall back to short prefix if description is too sparse
        prefix = name.split(":", 1)[0].strip()
        if is_good_alias(prefix):
            return prefix
        return None

    # All other styles: use the same logic as choose_best_alias
    return choose_best_alias(candidate)


def build_alias_paper_queries(
    user_query: str,
    dataset_candidates: list[DatasetCandidate],
    max_alias_queries: int = 3,
) -> list[str]:
    queries: list[str] = [user_query]
    seen: set[str] = {_normalize(user_query)}

    for candidate in dataset_candidates:
        if len(queries) >= 1 + max_alias_queries:
            break

        search_query = _choose_arXiv_query(candidate)
        if search_query is None:
            continue

        norm = _normalize(search_query)
        if norm in seen:
            continue

        seen.add(norm)
        queries.append(search_query)

    return queries
