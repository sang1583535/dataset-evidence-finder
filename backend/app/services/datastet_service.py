"""Defensive wrapper around the DataStet dataset-mention detector.

DataStet (a GROBID-related service) identifies dataset mentions in scientific
PDFs. It is used as the *first-choice* dataset-mention detector. Everything in
this module is intentionally defensive: any failure (service down, timeout,
unexpected response format) results in an empty list rather than an exception,
so the rest of the search pipeline keeps working with the existing
GROBID/rule-based extraction.

All DataStet endpoint and response-format assumptions are centralized here so
they can be adjusted in one place once the real API is confirmed.
"""

from __future__ import annotations

import json
from typing import Any, List, Optional

import requests

from app.core.config import DATASTET_URL
from app.services.cache_service import read_json_cache, write_json_cache
from app.services.fulltext_service import download_pdf


# --- Endpoint configuration -------------------------------------------------
# NOTE: The exact DataStet REST endpoint may differ between image versions.
# Keep the path here as a single constant so it is easy to change.
# Common candidates observed for DataStet / DataSeer-ml:
#   - /service/processDatastetPDF
#   - /api/processDatastetDocument
#   - /api/processFulltextDocument
#   - /api/annotate
# TODO: Confirm against the running `grobid/datastet` image and adjust.
DATASTET_PROCESS_ENDPOINT = f"{DATASTET_URL}/service/processDatastetPDF"

# Health/alive endpoint. DataStet typically exposes "/service/isalive".
# TODO: Confirm the actual health endpoint for the deployed image.
_ISALIVE_URL = f"{DATASTET_URL}/service/isalive"

# Cache configuration.
_CACHE_NAMESPACE = "datastet_mentions"
_DATASTET_TTL = 30 * 24 * 3600  # 30 days


# --- Bad-name filtering for merged dataset names ----------------------------
# Obvious non-dataset words that should never be treated as dataset names.
_BAD_DATASET_NAMES = {
    "vietnamese",
    "english",
    "these",
    "this",
    "experimental",
    "results",
    "dataset",
    "datasets",
    "corpus",
    "model",
    "system",
}


def is_datastet_available(timeout: int = 5) -> bool:
    """Return True if the DataStet service responds to a health check."""
    try:
        resp = requests.get(_ISALIVE_URL, timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False


def _post_pdf_bytes(pdf_bytes: bytes, timeout: int) -> Optional[requests.Response]:
    """POST PDF bytes to DataStet as multipart form data.

    Returns the response on HTTP 200, otherwise None. Never raises.
    """
    if not pdf_bytes:
        return None

    try:
        response = requests.post(
            DATASTET_PROCESS_ENDPOINT,
            files={"input": ("paper.pdf", pdf_bytes, "application/pdf")},
            timeout=timeout,
        )
    except Exception:
        return None

    if response.status_code != 200:
        return None

    return response


def _coerce_text(value: Any) -> str:
    """Best-effort extraction of a human-readable string from a value."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        # DataStet often nests the surface form under keys like these.
        for key in ("rawForm", "normalizedForm", "name", "text", "value"):
            sub = value.get(key)
            if isinstance(sub, str) and sub.strip():
                return sub.strip()
    return ""


def _build_mention(
    name: str,
    mention_text: str = "",
    context: str = "",
    mention_type: str = "dataset",
    section_title: Optional[str] = None,
) -> dict:
    name = (name or "").strip()
    mention_text = (mention_text or name).strip()
    return {
        "name": name,
        "mention_text": mention_text,
        "context": (context or "").strip(),
        "mention_type": mention_type or "dataset",
        "section_title": section_title,
        "source": "datastet",
    }


def _iter_mention_dicts(raw: Any):
    """Yield candidate mention dicts from common DataStet JSON shapes.

    DataStet responses vary by version. This tries several known shapes and is
    deliberately permissive. TODO: tighten once the real schema is confirmed.
    """
    if raw is None:
        return

    if isinstance(raw, list):
        for item in raw:
            yield from _iter_mention_dicts(item)
        return

    if not isinstance(raw, dict):
        return

    # Top-level containers that hold lists of mentions.
    for key in ("mentions", "datasets", "annotations", "entities"):
        value = raw.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item

    # Some responses group mentions by document/passage.
    for key in ("documents", "passages", "components"):
        value = raw.get(key)
        if isinstance(value, list):
            for item in value:
                yield from _iter_mention_dicts(item)


def normalize_datastet_mentions(raw_response: Any) -> List[dict]:
    """Normalize a DataStet response into a list of mention dicts.

    Accepts a parsed JSON object/list, a raw JSON string, or arbitrary text and
    returns mentions in the canonical shape used throughout the project:

        {
            "name": ...,
            "mention_text": ...,
            "context": ...,
            "mention_type": "dataset",
            "section_title": None,
            "source": "datastet",
        }

    Never raises; returns [] when nothing useful can be extracted.
    """
    if raw_response is None:
        return []

    parsed: Any = raw_response

    # Allow passing a raw string (JSON or otherwise).
    if isinstance(raw_response, (bytes, bytearray)):
        try:
            raw_response = raw_response.decode("utf-8", errors="ignore")
        except Exception:
            return []

    if isinstance(raw_response, str):
        text = raw_response.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except Exception:
            # Not JSON (e.g. TEI/XML or plain text). We cannot reliably parse
            # dataset mentions without the real schema, so stay defensive.
            # TODO: Add TEI/XML parsing once the DataStet output format is known.
            return []

    mentions: List[dict] = []
    seen: set[str] = set()

    for item in _iter_mention_dicts(parsed):
        # Surface form of the dataset name.
        name = (
            _coerce_text(item.get("rawForm"))
            or _coerce_text(item.get("normalizedForm"))
            or _coerce_text(item.get("name"))
            or _coerce_text(item.get("text"))
            or _coerce_text(item.get("dataset"))
        )
        if not name:
            continue

        context = (
            _coerce_text(item.get("context"))
            or _coerce_text(item.get("contextText"))
            or _coerce_text(item.get("sentence"))
        )
        mention_type = _coerce_text(item.get("type")) or "dataset"
        section_title = (
            _coerce_text(item.get("section"))
            or _coerce_text(item.get("sectionTitle"))
            or None
        )

        dedup_key = name.lower()
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        mentions.append(
            _build_mention(
                name=name,
                mention_text=name,
                context=context,
                mention_type=mention_type,
                section_title=section_title,
            )
        )

    return mentions


def extract_dataset_mentions_with_datastet_from_pdf_bytes(
    pdf_bytes: bytes,
    timeout: int = 120,
) -> List[dict]:
    """Send PDF bytes to DataStet and return normalized mentions.

    Never raises; returns [] on any failure.
    """
    response = _post_pdf_bytes(pdf_bytes, timeout=timeout)
    if response is None:
        return []

    content_type = (response.headers.get("Content-Type") or "").lower()

    try:
        if "json" in content_type:
            return normalize_datastet_mentions(response.json())
        # Fall back to parsing the raw text (handles JSON served without the
        # JSON content-type, and is a no-op for unrecognized formats).
        return normalize_datastet_mentions(response.text)
    except Exception:
        return []


def extract_dataset_mentions_with_datastet_from_pdf(
    pdf_url: str,
    timeout: int = 120,
) -> List[dict]:
    """Detect dataset mentions for a PDF URL via DataStet, with caching.

    Behavior:
      - If cached mentions exist for this pdf_url, return them.
      - Otherwise download the PDF (reusing fulltext_service.download_pdf),
        call DataStet, cache successful results, and return them.
      - Any failure returns [] without crashing.
    """
    if not pdf_url:
        return []

    cached = read_json_cache(_CACHE_NAMESPACE, _cache_key(pdf_url), ttl_seconds=_DATASTET_TTL)
    if cached is not None:
        return cached

    try:
        pdf_bytes = download_pdf(pdf_url)
    except Exception:
        return []

    mentions = extract_dataset_mentions_with_datastet_from_pdf_bytes(
        pdf_bytes, timeout=timeout
    )

    if mentions:
        write_json_cache(_CACHE_NAMESPACE, _cache_key(pdf_url), mentions)

    return mentions


def _cache_key(pdf_url: str) -> str:
    # The cache key is the pdf_url itself (hashed for a safe filename).
    from app.services.cache_service import make_cache_key

    return make_cache_key(pdf_url)


def _looks_like_dataset_name(name: str) -> bool:
    """Heuristic: keep dataset-like names, drop obvious generic words.

    A name is kept when it has an uppercase letter, a digit, a hyphen, or looks
    like an acronym. The bad-name filter is applied first.
    """
    if not name:
        return False

    stripped = name.strip()
    if len(stripped) < 2:
        return False

    if stripped.lower() in _BAD_DATASET_NAMES:
        return False

    if any(ch.isdigit() for ch in stripped):
        return True
    if "-" in stripped or "_" in stripped:
        return True
    if any(ch.isupper() for ch in stripped):
        return True

    return False


def merge_extracted_dataset_names(
    existing_names: List[str],
    datastet_names: List[str],
) -> List[str]:
    """Merge two lists of dataset names defensively.

    Rules:
      - Deduplicate case-insensitively.
      - Prefer longer, more specific forms (e.g. keep "VLSP 2016" over "VLSP").
      - Drop obvious non-dataset words (Vietnamese, English, These, ...).
      - Do not over-filter: keep names with uppercase letters, digits, hyphens
        or acronym-like patterns.

    DataStet names are considered first so they win when forms tie.
    """
    ordered: List[str] = []
    for name in list(datastet_names or []) + list(existing_names or []):
        if isinstance(name, str):
            cleaned = name.strip()
            if cleaned and _looks_like_dataset_name(cleaned):
                ordered.append(cleaned)

    selected: List[str] = []

    for name in ordered:
        norm = name.lower()
        skip = False
        replace_idx: Optional[int] = None

        for i, sel in enumerate(selected):
            sel_norm = sel.lower()
            if norm == sel_norm:
                skip = True
                break
            # Prefer the longer specific form when one name contains the other.
            if sel_norm in norm and _is_more_specific(name, sel):
                replace_idx = i
                break
            if norm in sel_norm and _is_more_specific(sel, name):
                skip = True
                break

        if skip:
            continue
        if replace_idx is not None:
            selected[replace_idx] = name
        else:
            selected.append(name)

    return selected


def _is_more_specific(longer: str, shorter: str) -> bool:
    """Return True if `longer` is a more specific form than `shorter`.

    Specifically, `shorter` appears as a whole-token prefix/substring of
    `longer` and `longer` has more tokens (e.g. "VLSP 2016" vs "VLSP").
    """
    long_norm = longer.lower()
    short_norm = shorter.lower()
    if short_norm not in long_norm:
        return False
    return len(long_norm.split()) > len(short_norm.split()) or len(long_norm) > len(
        short_norm
    )
