from typing import List

from app.models.schemas import DatasetCandidate
from app.services.alias_generator import generate_dataset_aliases


def _safe_get_attr(obj, names: list[str], default=None):
    for name in names:
        value = getattr(obj, name, None)

        if value:
            return value

    return default


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

    for resource_type in resource_types:
        if len(candidates) >= limit:
            break

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

            candidates.append(
                DatasetCandidate(
                    name=name,
                    source="European Language Grid",
                    url=url,
                    description=description,
                    tags=[resource_type, "ELG"],
                    aliases=generate_dataset_aliases(name),
                )
            )

            if len(candidates) >= limit:
                break

    return candidates