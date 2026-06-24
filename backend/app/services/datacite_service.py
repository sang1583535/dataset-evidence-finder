from typing import List

import requests

from app.models.schemas import DatasetCandidate
from app.services.alias_generator import generate_dataset_aliases


DATACITE_API_URL = "https://api.datacite.org/works"


def search_datacite_datasets(query: str, limit: int = 10) -> List[DatasetCandidate]:
    params = {
        "query": query,
        "resource-type-id": "dataset",
        "page[size]": limit,
    }

    response = requests.get(DATACITE_API_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    candidates = []

    for item in data.get("data", []):
        attrs = item.get("attributes", {})

        titles = attrs.get("titles", [])
        title = titles[0].get("title") if titles else None

        if not title:
            continue

        doi = attrs.get("doi")
        url = attrs.get("url") or (f"https://doi.org/{doi}" if doi else None)

        descriptions = attrs.get("descriptions", [])
        description = descriptions[0].get("description") if descriptions else None

        subjects = attrs.get("subjects", [])
        tags = [s.get("subject") for s in subjects if s.get("subject")]

        candidates.append(
            DatasetCandidate(
                name=title,
                source="DataCite",
                url=url,
                description=description,
                tags=tags,
                aliases=generate_dataset_aliases(title),
            )
        )

    return candidates