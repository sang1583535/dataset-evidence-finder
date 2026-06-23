import requests


BACKEND_URL = "http://localhost:8000/api"


def search_datasets(
    query: str,
    max_datasets: int,
    max_papers: int,
    use_full_text: bool,
    use_datacite: bool,
):
    payload = {
        "query": query,
        "max_datasets": max_datasets,
        "max_papers": max_papers,
        "use_full_text": use_full_text,
        "use_datacite": use_datacite,
    }

    response = requests.post(
        f"{BACKEND_URL}/search",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    return response.json()


def get_reference_catalogues():
    response = requests.get(
        f"{BACKEND_URL}/reference-catalogues",
        timeout=20,
    )
    response.raise_for_status()

    return response.json()