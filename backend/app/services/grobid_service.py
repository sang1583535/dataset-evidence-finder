from __future__ import annotations

from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from app.core.config import GROBID_URL
from app.services.cache_service import make_cache_key, read_json_cache, write_json_cache

GROBID_PROCESS_FULLTEXT_ENDPOINT = f"{GROBID_URL}/api/processFulltextDocument"
_ISALIVE_URL = f"{GROBID_URL}/api/isalive"
_TIMEOUT = 60
_GROBID_TTL = 30 * 24 * 3600


@dataclass
class GrobidSection:
    title: str
    text: str


def is_grobid_available() -> bool:
    try:
        resp = requests.get(_ISALIVE_URL, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _parse_tei(tei_xml: str) -> list[GrobidSection]:
    soup = BeautifulSoup(tei_xml, "lxml-xml")
    sections: list[GrobidSection] = []

    body = soup.find("body")
    if not body:
        return sections

    for div in body.find_all("div"):
        head = div.find("head")
        section_title = head.get_text(strip=True) if head else ""

        paragraphs = div.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
        if text.strip():
            sections.append(GrobidSection(title=section_title, text=text.strip()))

    return sections


def extract_fulltext_sections(pdf_url: str, pdf_bytes: bytes) -> list[GrobidSection]:
    cache_key = make_cache_key(pdf_url, "grobid")
    cached = read_json_cache("grobid_sections", cache_key, ttl_seconds=_GROBID_TTL)

    if cached is not None:
        return [GrobidSection(**item) for item in cached]

    response = requests.post(
        GROBID_PROCESS_FULLTEXT_ENDPOINT,
        files={"input": ("paper.pdf", pdf_bytes, "application/pdf")},
        timeout=_TIMEOUT,
    )
    response.raise_for_status()

    sections = _parse_tei(response.text)

    if sections:
        write_json_cache(
            "grobid_sections",
            cache_key,
            [{"title": s.title, "text": s.text} for s in sections],
        )

    return sections
