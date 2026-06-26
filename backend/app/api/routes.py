import shutil

from fastapi import APIRouter

from app.core.config import (
    GROBID_URL,
    MAX_SECOND_PASS_DATASET_QUERIES,
    MAX_SECOND_PASS_RESULTS_PER_SOURCE,
)
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    SecondPassRequest,
    SecondPassResponse,
)
from app.services.hf_service import search_huggingface_datasets
from app.services.datacite_service import search_datacite_datasets
from app.services.arxiv_service import search_arxiv_papers
from app.services.paper_service import extract_evidence_for_papers
from app.services.openml_service import search_openml_datasets
from app.services.elg_service import search_elg_resources
from app.services.matcher import match_datasets_with_evidence
from app.services.cache_service import CACHE_ROOT
from app.services.query_expansion import build_alias_paper_queries
from app.services.dataset_expansion import (
    extract_second_pass_queries_from_evidence,
    second_pass_dataset_lookup,
    deduplicate_dataset_candidates,
)
from app.services.grobid_service import is_grobid_available

router = APIRouter()


def _apply_second_pass(
    query: str,
    dataset_candidates: list,
    evidence: list,
    use_elg: bool,
    use_openml: bool,
    use_datacite: bool,
):
    """Run the second-pass dataset lookup and re-match against evidence.

    Returns (queries, merged_candidates, matches). Limits come from config.
    """
    queries = extract_second_pass_queries_from_evidence(
        evidence,
        max_queries=MAX_SECOND_PASS_DATASET_QUERIES,
    )

    second_pass_candidates = second_pass_dataset_lookup(
        queries=queries,
        use_elg=use_elg,
        use_openml=use_openml,
        use_datacite=use_datacite,
        max_results_per_source=MAX_SECOND_PASS_RESULTS_PER_SOURCE,
    )

    merged_candidates = deduplicate_dataset_candidates(
        dataset_candidates + second_pass_candidates
    )

    matches = match_datasets_with_evidence(
        datasets=merged_candidates,
        evidence_items=evidence,
    )

    return queries, merged_candidates, matches


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    dataset_candidates = []

    hf_datasets = search_huggingface_datasets(
        query=request.query,
        limit=request.max_datasets,
    )
    dataset_candidates.extend(hf_datasets)

    if request.use_elg:
        elg_datasets = search_elg_resources(
            query=request.query,
            limit=request.max_datasets,
        )
        dataset_candidates.extend(elg_datasets)

    if request.use_openml:
        openml_datasets = search_openml_datasets(
            query=request.query,
            limit=request.max_datasets,
        )
        dataset_candidates.extend(openml_datasets)

    if request.use_datacite:
        datacite_datasets = search_datacite_datasets(
            query=request.query,
            limit=request.max_datasets,
        )
        dataset_candidates.extend(datacite_datasets)

    if request.use_dataset_aliases_for_paper_search:
        paper_queries = build_alias_paper_queries(
            request.query, dataset_candidates, request.max_alias_queries
        )
    else:
        paper_queries = [request.query]

    seen_arxiv_ids: set[str] = set()
    all_papers = []

    for pq in paper_queries:
        try:
            pq_papers = search_arxiv_papers(query=pq, max_results=request.max_papers)
        except Exception:
            continue
        for paper in pq_papers:
            if paper.arxiv_id not in seen_arxiv_ids:
                seen_arxiv_ids.add(paper.arxiv_id)
                all_papers.append(paper)

    evidence = extract_evidence_for_papers(
        papers=all_papers,
        use_full_text=request.use_full_text,
    )

    matches = match_datasets_with_evidence(
        datasets=dataset_candidates,
        evidence_items=evidence,
    )

    second_pass_queries: list[str] = []
    if request.use_second_pass_dataset_lookup:
        second_pass_queries, dataset_candidates, matches = _apply_second_pass(
            query=request.query,
            dataset_candidates=dataset_candidates,
            evidence=evidence,
            use_elg=request.use_elg,
            use_openml=request.use_openml,
            use_datacite=request.use_datacite,
        )

    return SearchResponse(
        query=request.query,
        dataset_candidates=dataset_candidates,
        paper_evidence=evidence,
        matched_results=matches,
        paper_queries=paper_queries,
        second_pass_dataset_queries=second_pass_queries,
    )


@router.post("/search/second-pass", response_model=SecondPassResponse)
def search_second_pass(request: SecondPassRequest):
    """Run only the second-pass dataset lookup against existing evidence.

    This lets the frontend render first-pass results immediately and append
    the second pass afterwards, instead of waiting for the whole pipeline.
    """
    queries, merged_candidates, matches = _apply_second_pass(
        query=request.query,
        dataset_candidates=list(request.dataset_candidates),
        evidence=list(request.paper_evidence),
        use_elg=request.use_elg,
        use_openml=request.use_openml,
        use_datacite=request.use_datacite,
    )

    return SecondPassResponse(
        second_pass_dataset_queries=queries,
        dataset_candidates=merged_candidates,
        matched_results=matches,
    )


@router.get("/grobid/status")
def grobid_status():
    return {"available": is_grobid_available(), "url": GROBID_URL}


_CACHE_NAMESPACES = [
    "arxiv_search",
    "pdf_text",
    "grobid_sections",
    "hf_search",
    "elg_search",
    "openml_search",
    "datacite_search",
]


@router.get("/cache/stats")
def cache_stats():
    namespaces = {}

    for ns in _CACHE_NAMESPACES:
        ns_path = CACHE_ROOT / ns
        if ns_path.exists():
            files = list(ns_path.glob("*.json"))
            size_bytes = sum(f.stat().st_size for f in files)
            namespaces[ns] = {"files": len(files), "size_bytes": size_bytes}
        else:
            namespaces[ns] = {"files": 0, "size_bytes": 0}

    return {
        "enabled": True,
        "cache_root": str(CACHE_ROOT.resolve()),
        "namespaces": namespaces,
    }


@router.delete("/cache")
def clear_cache():
    if CACHE_ROOT.exists():
        shutil.rmtree(CACHE_ROOT)
    return {"status": "cache_cleared"}