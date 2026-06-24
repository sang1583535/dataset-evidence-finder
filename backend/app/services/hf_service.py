from typing import List
from huggingface_hub import HfApi

from app.models.schemas import DatasetCandidate
from app.services.alias_generator import generate_dataset_aliases


def search_huggingface_datasets(query: str, limit: int = 10) -> List[DatasetCandidate]:
    api = HfApi()
    results = api.list_datasets(search=query, limit=limit)

    candidates = []

    for item in results:
        dataset_id = getattr(item, "id", None)

        if not dataset_id:
            continue

        candidates.append(
            DatasetCandidate(
                name=dataset_id,
                source="Hugging Face",
                url=f"https://huggingface.co/datasets/{dataset_id}",
                description=getattr(item, "description", None),
                tags=getattr(item, "tags", []) or [],
                aliases=generate_dataset_aliases(dataset_id),
            )
        )

    return candidates