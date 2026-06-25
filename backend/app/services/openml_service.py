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


def search_openml_datasets(query: str, limit: int = 10) -> List[DatasetCandidate]:
    candidates = []

    try:
        datasets = openml.datasets.list_datasets(output_format="dataframe")
    except Exception:
        return candidates

    if datasets is None or datasets.empty:
        return candidates

    query_terms = [t for t in query.lower().split() if len(t) > 2]

    if not query_terms:
        return candidates

    name_col = datasets["name"].str.lower()

    mask = name_col.apply(
        lambda n: any(t in n for t in query_terms) and any(term in n for term in NLP_CL_TERMS)
    )
    filtered = datasets[mask].copy()

    if filtered.empty:
        return candidates

    if "NumberOfInstances" in filtered.columns:
        filtered = filtered.sort_values(
            "NumberOfInstances", ascending=False, na_position="last"
        )

    for _, row in filtered.head(limit).iterrows():
        name = str(row.get("name", "")).strip()
        dataset_id = row.get("did")

        if not name or not dataset_id:
            continue

        tags = ["OpenML"]

        n_instances = row.get("NumberOfInstances")
        n_features = row.get("NumberOfFeatures")

        if n_instances is not None and str(n_instances) != "nan":
            tags.append(f"instances:{int(n_instances)}")
        if n_features is not None and str(n_features) != "nan":
            tags.append(f"features:{int(n_features)}")

        candidates.append(
            DatasetCandidate(
                name=name,
                source="OpenML",
                url=f"https://www.openml.org/d/{int(dataset_id)}",
                description=None,
                tags=tags,
                aliases=generate_dataset_aliases(name),
            )
        )

    return candidates
