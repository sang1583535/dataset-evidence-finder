from typing import List
from urllib.parse import quote
import time

import feedparser
import requests

from app.models.schemas import PaperMetadata
from app.services.cache_service import make_cache_key, read_json_cache, write_json_cache


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_HEADERS = {
    "User-Agent": "NLP-CL-Dataset-Evidence-Finder/1.0 (contact: local-app)",
}

_ARXIV_TTL = 24 * 3600


def extract_arxiv_id(entry_id: str) -> str:
    """
    Example entry_id:
    http://arxiv.org/abs/2406.05967v2

    Return:
    2406.05967
    """
    raw_id = entry_id.rstrip("/").split("/")[-1]
    return raw_id.split("v")[0]


def _build_search_query(query: str) -> str:
    terms = [t for t in query.split() if len(t) > 1]
    if not terms:
        return f'all:"{query}" AND cat:cs.CL'
    term_clause = " AND ".join(f"all:{t}" for t in terms)
    return f"({term_clause}) AND cat:cs.CL"


def search_arxiv_papers(query: str, max_results: int = 5) -> List[PaperMetadata]:
    cache_key = make_cache_key(query, str(max_results))
    cached = read_json_cache("arxiv_search", cache_key, ttl_seconds=_ARXIV_TTL)

    if cached is not None:
        return [PaperMetadata(**item) for item in cached]

    search_query = _build_search_query(query)

    url = (
        f"{ARXIV_API_URL}"
        f"?search_query={quote(search_query)}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy=relevance"
        f"&sortOrder=descending"
    )

    max_retries = 2
    response = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=30, headers=ARXIV_HEADERS)
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return []
        except requests.exceptions.RequestException:
            return []

        if response.status_code != 429:
            break

        if attempt < max_retries:
            time.sleep(1.5 * (attempt + 1))
            continue

        return []

    if response is None:
        return []

    response.raise_for_status()

    feed = feedparser.parse(response.text)

    papers = []

    for entry in feed.entries:
        arxiv_id = extract_arxiv_id(entry.id)

        papers.append(
            PaperMetadata(
                arxiv_id=arxiv_id,
                title=entry.title.replace("\n", " ").strip(),
                summary=entry.summary.replace("\n", " ").strip(),
                url=entry.link,
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
            )
        )

    if papers:
        serialized = [
            p.model_dump() if hasattr(p, "model_dump") else p.dict()
            for p in papers
        ]
        write_json_cache("arxiv_search", cache_key, serialized)

    return papers
