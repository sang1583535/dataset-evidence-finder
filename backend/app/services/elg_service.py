from typing import List

from app.models.schemas import DatasetCandidate
from app.services.alias_generator import generate_dataset_aliases, normalize_text


def _significant_query_tokens(query: str) -> list[str]:
    """Meaningful tokens from the query, ignoring pure numbers/years.

    ELG's catalog search is a loose full-text match, so a query like
    "VLSP 2016" can return unrelated resources that only share the year
    "2016" (e.g. "Walenty (2016-04-28)"). We use the non-numeric tokens
    (e.g. "vlsp") to verify a result is actually relevant.
    """
    tokens = normalize_text(query).split()
    return [t for t in tokens if len(t) >= 3 and not t.isdigit()]


def _is_relevant_to_query(name: str, query: str) -> bool:
    significant = _significant_query_tokens(query)
    if not significant:
        # Nothing meaningful to filter on; keep the original behaviour.
        return True
    normalized_name = normalize_text(name)
    return any(token in normalized_name for token in significant)


def _safe_get_attr(obj, names: list[str], default=None):
    for name in names:
        value = getattr(obj, name, None)
        if value:
            return value
    return default


def _get_popularity_score(entity) -> int:
    for attr in ("download_count", "downloads", "views", "view_count", "usage_count"):
        val = getattr(entity, attr, None)
        if val is not None:
            try:
                return int(val)
            except (TypeError, ValueError):
                continue
    return 0


def search_elg_resources(query: str, limit: int = 10) -> List[DatasetCandidate]:
    candidates = []

    try:
        from elg import Catalog
    except Exception:
        return candidates

    try:
        catalog = Catalog()
    except Exception:
        return candidates

    resource_types = [
        "Corpus",
        "Lexical/Conceptual resource",
        "Language description",
    ]

    collected = []

    for resource_type in resource_types:
        try:
            results = catalog.search(
                search=query,
                resource=resource_type,
                limit=limit,
            )
        except Exception:
            continue

        for entity in results:
            name = _safe_get_attr(
                entity,
                ["resource_name", "name", "title"],
                default=str(entity),
            )
            description = _safe_get_attr(
                entity,
                ["description", "short_description"],
                default=None,
            )
            url = _safe_get_attr(
                entity,
                ["landing_page", "url"],
                default=None,
            )
            name = str(name).strip()

            if not name:
                continue

            if not _is_relevant_to_query(name, query):
                continue

            popularity = _get_popularity_score(entity)

            collected.append(
                (
                    popularity,
                    DatasetCandidate(
                        name=name,
                        source="European Language Grid",
                        url=url,
                        description=description,
                        tags=[resource_type, "ELG"],
                        aliases=generate_dataset_aliases(name),
                    ),
                )
            )

    collected.sort(key=lambda x: x[0], reverse=True)

    for _, candidate in collected[:limit]:
        candidates.append(candidate)

    return candidates
