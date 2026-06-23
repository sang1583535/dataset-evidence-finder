from fastapi import APIRouter

from app.models.schemas import SearchRequest, SearchResponse
from app.services.hf_service import search_huggingface_datasets
from app.services.datacite_service import search_datacite_datasets
from app.services.arxiv_service import search_arxiv_papers
from app.services.paper_service import extract_evidence_for_papers
from app.services.matcher import match_datasets_with_evidence
from app.services.source_catalogue import get_reference_catalogues

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


@router.get("/reference-catalogues")
def reference_catalogues():
    return get_reference_catalogues()