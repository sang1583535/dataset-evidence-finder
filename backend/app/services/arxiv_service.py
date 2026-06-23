from typing import List
from urllib.parse import quote

import feedparser
import requests

from app.models.schemas import PaperMetadata


ARXIV_API_URL = "http://export.arxiv.org/api/query"


def extract_arxiv_id(entry_id: str) -> str:
    """
    Example entry_id:
    http://arxiv.org/abs/2406.05967v2

    Return:
    2406.05967
    """
    raw_id = entry_id.rstrip("/").split("/")[-1]
    return raw_id.split("v")[0]


def search_arxiv_papers(query: str, max_results: int = 5) -> List[PaperMetadata]:
    search_query = f'all:"{query}" AND cat:cs.CL'

    url = (
        f"{ARXIV_API_URL}"
        f"?search_query={quote(search_query)}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy=relevance"
        f"&sortOrder=descending"
    )

    response = requests.get(url, timeout=30)
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

    return papers