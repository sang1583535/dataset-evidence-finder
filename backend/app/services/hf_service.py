from typing import List

from huggingface_hub import HfApi

from app.models.schemas import DatasetCandidate
from app.services.alias_generator import generate_dataset_aliases


def search_huggingface_datasets(query: str, limit: int = 10) -> List[DatasetCandidate]:
    candidates = []

    try:
        api = HfApi()
        # sort="downloads" returns most-downloaded first (descending by default)
        results = list(api.list_datasets(search=query, sort="downloads", limit=limit))
    except Exception:
        return candidates

    for item in results:
        dataset_id = getattr(item, "id", None)

        if not dataset_id:
            continue

        tags = list(getattr(item, "tags", []) or [])

        downloads = getattr(item, "downloads", None)
        likes = getattr(item, "likes", None)

        if downloads is not None:
            tags.append(f"downloads:{downloads}")
        if likes is not None:
            tags.append(f"likes:{likes}")

        candidates.append(
            DatasetCandidate(
                name=dataset_id,
                source="Hugging Face",
                url=f"https://huggingface.co/datasets/{dataset_id}",
                description=getattr(item, "description", None),
                tags=tags,
                aliases=generate_dataset_aliases(dataset_id),
            )
        )

    return candidates
