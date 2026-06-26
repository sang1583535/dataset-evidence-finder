from app.models.schemas import DatasetCandidate, PaperEvidence
from app.services.dataset_expansion import (
    deduplicate_dataset_candidates,
    extract_second_pass_queries_from_evidence,
    is_valid_second_pass_query,
    second_pass_dataset_lookup,
)


def test_extract_prefers_acronym_year_forms():
    evidence = [
        PaperEvidence(
            paper_title="Sample Paper",
            paper_url="https://example.com/paper",
            evidence_sentence=(
                "We evaluate the proposed model on two datasets: "
                "VLSP 2016 and AIVIVN 2019."
            ),
            extracted_dataset_names=["AIVIVN", "VLSP"],
            score=5,
            source_text_type="grobid_full_text",
            section_title="Results and Discussion",
        )
    ]

    queries = extract_second_pass_queries_from_evidence(evidence, max_queries=3)

    assert "VLSP 2016" in queries
    assert "AIVIVN 2019" in queries
    # Shorter forms must not also appear alongside the longer specific forms.
    assert "VLSP" not in queries
    assert "AIVIVN" not in queries


def test_invalid_names_are_filtered():
    evidence = [
        PaperEvidence(
            paper_title="Sample Paper",
            paper_url="https://example.com/paper",
            evidence_sentence="",
            extracted_dataset_names=[
                "Vietnamese",
                "These",
                "e-commerce",
                "VLSP",
                "AIVIVN",
            ],
            score=5,
            source_text_type="grobid_full_text",
            section_title="Datasets",
        )
    ]

    queries = extract_second_pass_queries_from_evidence(evidence, max_queries=5)

    assert "VLSP" in queries
    assert "AIVIVN" in queries
    assert "Vietnamese" not in queries
    assert "These" not in queries
    assert "e-commerce" not in queries

    assert is_valid_second_pass_query("VLSP") is True
    assert is_valid_second_pass_query("AIVIVN") is True
    assert is_valid_second_pass_query("Vietnamese") is False
    assert is_valid_second_pass_query("These") is False
    assert is_valid_second_pass_query("e-commerce") is False


def test_abstract_evidence_has_lower_priority():
    abstract_evidence = PaperEvidence(
        paper_title="Sample Paper",
        paper_url="https://example.com/paper",
        evidence_sentence=(
            "Experimental results on the VLSP 2016 and AIVIVN 2019 "
            "datasets demonstrate..."
        ),
        score=3,
        source_text_type="abstract",
        section_title=None,
    )

    # Abstract-only evidence can still be used as a fallback.
    abstract_only = extract_second_pass_queries_from_evidence(
        [abstract_evidence], max_queries=3
    )
    assert "VLSP 2016" in abstract_only
    assert "AIVIVN 2019" in abstract_only

    # When better grobid_full_text evidence exists, it comes first.
    full_text_evidence = PaperEvidence(
        paper_title="Another Paper",
        paper_url="https://example.com/paper2",
        evidence_sentence="We use the FLORES-200 benchmark for evaluation.",
        extracted_dataset_names=["FLORES-200"],
        score=5,
        source_text_type="grobid_full_text",
        section_title="Evaluation",
    )

    combined = extract_second_pass_queries_from_evidence(
        [abstract_evidence, full_text_evidence], max_queries=1
    )
    assert combined == ["FLORES-200"]


def test_deduplicate_dataset_candidates():
    candidates = [
        DatasetCandidate(
            name="VLSP 2016",
            source="Hugging Face",
            url="https://huggingface.co/datasets/vlsp-2016",
        ),
        DatasetCandidate(
            name="VLSP 2016",
            source="Hugging Face",
            url="https://huggingface.co/datasets/vlsp-2016",
        ),
        DatasetCandidate(
            name="AIVIVN 2019",
            source="Hugging Face",
            url="https://huggingface.co/datasets/aivivn-2019",
        ),
    ]

    deduped = deduplicate_dataset_candidates(candidates)

    assert len(deduped) == 2
    names = sorted(c.name for c in deduped)
    assert names == ["AIVIVN 2019", "VLSP 2016"]


def test_second_pass_adds_query_as_alias(monkeypatch):
    import app.services.hf_service as hf_service
    from app.services.matcher import match_datasets_with_evidence

    # Simulate Hugging Face returning a repo-id style name whose generated
    # aliases normalize differently from the evidence wording "VLSP 2016".
    def fake_hf_search(query: str, limit: int = 10):
        return [
            DatasetCandidate(
                name="uitnlp/VLSP2016_sentiment",
                source="Hugging Face",
                url="https://huggingface.co/datasets/uitnlp/VLSP2016_sentiment",
                aliases=["uitnlp/VLSP2016_sentiment", "VLSP2016 sentiment"],
            )
        ]

    monkeypatch.setattr(hf_service, "search_huggingface_datasets", fake_hf_search)
    # Avoid reading/writing the on-disk cache during the test.
    monkeypatch.setattr(
        "app.services.dataset_expansion.read_json_cache", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "app.services.dataset_expansion.write_json_cache", lambda *a, **k: None
    )

    candidates = second_pass_dataset_lookup(
        queries=["VLSP 2016"],
        use_elg=False,
        use_openml=False,
        use_datacite=False,
        max_results_per_source=2,
    )

    assert len(candidates) == 1
    assert "VLSP 2016" in candidates[0].aliases

    evidence = [
        PaperEvidence(
            paper_title="Expanding Vietnamese SentiWordNet",
            paper_url="https://example.com/paper",
            evidence_sentence="We evaluate our models on the VLSP 2016 dataset.",
            source_text_type="grobid_full_text",
            section_title="Experiments",
        )
    ]

    matches = match_datasets_with_evidence(
        datasets=candidates,
        evidence_items=evidence,
    )

    assert len(matches) == 1
    assert matches[0].dataset_name == "uitnlp/VLSP2016_sentiment"
    assert matches[0].evidences[0].matched_alias == "VLSP 2016"
