from typing import List, Optional
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    max_datasets: int = 10
    max_papers: int = 5
    use_full_text: bool = True
    use_datacite: bool = False


class DatasetCandidate(BaseModel):
    name: str
    source: str
    url: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    aliases: List[str] = []


class PaperMetadata(BaseModel):
    arxiv_id: str
    title: str
    summary: str
    url: str
    pdf_url: str


class PaperEvidence(BaseModel):
    paper_title: str
    paper_url: str
    evidence_sentence: str
    extracted_dataset_names: List[str] = []
    score: int = 0
    source_text_type: str = "abstract"


class MatchedResult(BaseModel):
    dataset_name: str
    matched_alias: str
    dataset_source: str
    dataset_url: Optional[str] = None
    paper_title: Optional[str] = None
    paper_url: Optional[str] = None
    evidence_sentence: Optional[str] = None
    match_type: str
    match_score: float = 0.0


class SearchResponse(BaseModel):
    query: str
    dataset_candidates: List[DatasetCandidate]
    paper_evidence: List[PaperEvidence]
    matched_results: List[MatchedResult]