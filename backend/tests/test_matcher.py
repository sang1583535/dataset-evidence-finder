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
    assert matches[0].dataset_name == "m-a-p/MAP-CC"
    assert matches[0].paper_url == "https://example.com"
    assert matches[0].evidence_count == 1
    assert len(matches[0].evidences) == 1
    assert matches[0].evidences[0].matched_alias in ["MAP-CC", "MAP CC"]


def test_match_groups_by_dataset_paper_and_deduplicates_evidence_sentences():
    datasets = [
        DatasetCandidate(
            name="m-a-p/MAP-CC",
            source="Hugging Face",
            aliases=["MAP-CC", "MAP CC"],
        )
    ]

    evidence = [
        PaperEvidence(
            paper_title="Example Paper",
            paper_url="https://arxiv.org/abs/1234.5678",
            evidence_sentence="We use MAP-CC as the multilingual corpus.",
            score=6,
            source_text_type="full_text_pdf",
        ),
        PaperEvidence(
            paper_title="Example Paper",
            paper_url="https://arxiv.org/abs/1234.5678",
            evidence_sentence="The MAP-CC dataset contains multilingual web data.",
            score=4,
            source_text_type="full_text_pdf",
        ),
        PaperEvidence(
            paper_title="Example Paper",
            paper_url="https://arxiv.org/abs/1234.5678",
            evidence_sentence="The MAP-CC dataset contains multilingual web data.",
            score=4,
            source_text_type="full_text_pdf",
        ),
    ]

    matches = match_datasets_with_evidence(datasets, evidence)

    assert len(matches) == 1
    assert matches[0].evidence_count == 2
    assert len(matches[0].evidences) == 2