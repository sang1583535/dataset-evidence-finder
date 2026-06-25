import fitz
import requests

from app.services.cache_service import make_cache_key, read_json_cache, write_json_cache


_PDF_TTL = 30 * 24 * 3600


def download_pdf(pdf_url: str) -> bytes:
    response = requests.get(pdf_url, timeout=40)
    response.raise_for_status()
    return response.content


def extract_text_from_pdf_bytes(pdf_bytes: bytes, max_pages: int = 12) -> str:
    text_parts = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        page_count = min(len(doc), max_pages)

        for page_index in range(page_count):
            page = doc[page_index]
            text_parts.append(page.get_text())

    return "\n".join(text_parts)


def get_pdf_text(pdf_url: str, max_pages: int = 12) -> str:
    cache_key = make_cache_key(pdf_url, str(max_pages))
    cached = read_json_cache("pdf_text", cache_key, ttl_seconds=_PDF_TTL)

    if cached is not None:
        return cached

    pdf_bytes = download_pdf(pdf_url)
    text = extract_text_from_pdf_bytes(pdf_bytes, max_pages=max_pages)

    if text:
        write_json_cache("pdf_text", cache_key, text)

    return text
