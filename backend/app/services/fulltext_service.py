import fitz
import requests


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
    pdf_bytes = download_pdf(pdf_url)
    return extract_text_from_pdf_bytes(pdf_bytes, max_pages=max_pages)