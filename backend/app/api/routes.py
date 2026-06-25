import shutil

from fastapi import APIRouter

from app.models.schemas import SearchRequest, SearchResponse
from app.services.hf_service import search_huggingface_datasets
from app.services.datacite_service import search_datacite_datasets
from app.services.arxiv_service import search_arxiv_papers
from app.services.paper_service import extract_evidence_for_papers
from app.services.openml_service import search_openml_datasets
from app.services.elg_service import search_elg_resources
from app.services.matcher import match_datasets_with_evidence
from app.services.cache_service import CACHE_ROOT

router = APIRouter()


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

    papers = search_arxiv_papers(
        query=request.query,
        max_results=request.max_papers,
    )

    evidence = extract_evidence_for_papers(
        papers=papers,
        use_full_text=request.use_full_text,
    )

    matches = match_datasets_with_evidence(
        datasets=dataset_candidates,
        evidence_items=evidence,
    )

    return SearchResponse(
        query=request.query,
        dataset_candidates=dataset_candidates,
        paper_evidence=evidence,
        matched_results=matches,
    )


_CACHE_NAMESPACES = ["arxiv_search", "pdf_text"]


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