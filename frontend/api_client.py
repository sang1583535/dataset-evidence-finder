import os

import requests


BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api")


def search_datasets(
    query: str,
    max_datasets: int,
    max_papers: int,
    use_full_text: bool,
    use_datacite: bool,
    use_openml: bool,
    use_elg: bool,
    use_dataset_aliases_for_paper_search: bool = True,
    max_alias_queries: int = 3,
    use_second_pass_dataset_lookup: bool = False,
):
    payload = {
        "query": query,
        "max_datasets": max_datasets,
        "max_papers": max_papers,
        "use_full_text": use_full_text,
        "use_datacite": use_datacite,
        "use_openml": use_openml,
        "use_elg": use_elg,
        "use_dataset_aliases_for_paper_search": use_dataset_aliases_for_paper_search,
        "max_alias_queries": max_alias_queries,
        "use_second_pass_dataset_lookup": use_second_pass_dataset_lookup,
    }

    response = requests.post(
        f"{BACKEND_URL}/search",
        json=payload,
        timeout=180,
    )
    response.raise_for_status()

    return response.json()


def run_second_pass(
    query: str,
    dataset_candidates: list,
    paper_evidence: list,
    use_datacite: bool,
    use_openml: bool,
    use_elg: bool,
):
    payload = {
        "query": query,
        "dataset_candidates": dataset_candidates,
        "paper_evidence": paper_evidence,
        "use_datacite": use_datacite,
        "use_openml": use_openml,
        "use_elg": use_elg,
    }

    response = requests.post(
        f"{BACKEND_URL}/search/second-pass",
        json=payload,
        timeout=180,
    )
    response.raise_for_status()

    return response.json()
