from app.models.schemas import DatasetCandidate, PaperEvidence
from app.services.matcher import match_datasets_with_evidence


def test_match_hf_short_alias_with_paper_sentence():
    datasets = [
        DatasetCandidate(
            name="m-a-p/MAP-CC",
            source="Hugging Face",
            aliases=["MAP-CC", "MAP CC"],
        )
    ]

    evidence = [
        PaperEvidence(
            paper_title="Test Paper",
            paper_url="https://example.com",
            evidence_sentence="We use MAP-CC as the main multilingual corpus.",
            score=5,
            source_text_type="full_text_pdf",
        )
    ]

    matches = match_datasets_with_evidence(datasets, evidence)

    assert len(matches) == 1
    assert matches[0].matched_alias in ["MAP-CC", "MAP CC"]