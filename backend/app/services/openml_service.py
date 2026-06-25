from typing import List

import openml

from app.models.schemas import DatasetCandidate
from app.services.alias_generator import generate_dataset_aliases


NLP_CL_TERMS = [
    "text",
    "nlp",
    "natural language",
    "language",
    "sentiment",
    "document",
    "corpus",
    "news",
    "tweet",
    "twitter",
    "review",
    "spam",
    "topic",
    "translation",
    "speech",
]


def is_nlp_cl_related(name: str, description: str | None = None) -> bool:
    combined = f"{name} {description or ''}".lower()
    return any(term in combined for term in NLP_CL_TERMS)


def query_matches_dataset(query: str, name: str, description: str | None = None) -> bool:
    query_terms = [term for term in query.lower().split() if len(term) > 2]
    combined = f"{name} {description or ''}".lower()
    return any(term in combined for term in query_terms)


def safe_get_openml_description(dataset_id: int) -> str | None:
    try:
        dataset = openml.datasets.get_dataset(
            dataset_id,
            download_data=False,
            download_qualities=False,
            download_features_meta_data=False,
        )
        return getattr(dataset, "description", None)
    except Exception:
        return None


def search_openml_datasets(query: str, limit: int = 10) -> List[DatasetCandidate]:
    candidates = []

    try:
        datasets = openml.datasets.list_datasets(output_format="dataframe")
    except Exception:
        return candidates

    if datasets is None or datasets.empty:
        return candidates

    for _, row in datasets.iterrows():
        name = str(row.get("name", "")).strip()

        if not name:
            continue

        dataset_id = row.get("did")

        if not dataset_id:
            continue

        if not query_matches_dataset(query, name):
            continue

        description = safe_get_openml_description(int(dataset_id))

        if not is_nlp_cl_related(name, description):
            continue

        url = f"https://www.openml.org/d/{int(dataset_id)}"

        tags = ["OpenML"]

        if row.get("NumberOfInstances") is not None:
            tags.append(f"instances:{row.get('NumberOfInstances')}")

        if row.get("NumberOfFeatures") is not None:
            tags.append(f"features:{row.get('NumberOfFeatures')}")

        candidates.append(
            DatasetCandidate(
                name=name,
                source="OpenML",
                url=url,
                description=description,
                tags=tags,
                aliases=generate_dataset_aliases(name),
            )
        )

        if len(candidates) >= limit:
            break

    return candidates