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


# --- new precision tests ---


def test_false_positive_generic_alias_does_not_match():
    """nlg-machine-translation and machine translation are generic; should produce no match."""
    datasets = [
        DatasetCandidate(
            name="aisingapore/NLG-Machine-Translation",
            source="Hugging Face",
            aliases=["NLG-Machine-Translation", "nlg-machine-translation", "machine translation"],
        )
    ]

    evidence = [
        PaperEvidence(
            paper_title="Beam Search Strategies for Neural Machine Translation",
            paper_url="https://arxiv.org/abs/1234.0001",
            evidence_sentence=(
                "The basic concept in Neural Machine Translation (NMT) is to train a large "
                "Neural Network that maximizes the translation performance on a given parallel corpus."
            ),
            score=3,
            source_text_type="abstract",
        )
    ]

    matches = match_datasets_with_evidence(datasets, evidence)

    assert len(matches) == 0


def test_real_dataset_alias_matches_usage_sentence():
    """MAP-CC with explicit usage context should produce one match."""
    datasets = [
        DatasetCandidate(
            name="m-a-p/MAP-CC",
            source="Hugging Face",
            aliases=["MAP-CC", "MAP CC"],
        )
    ]

    evidence = [
        PaperEvidence(
            paper_title="Multilingual Pretraining",
            paper_url="https://arxiv.org/abs/1234.0002",
            evidence_sentence="We use MAP-CC as the main multilingual corpus for training.",
            score=5,
            source_text_type="full_text_pdf",
        )
    ]

    matches = match_datasets_with_evidence(datasets, evidence)

    assert len(matches) == 1


def test_fuzzy_does_not_match_generic_alias():
    """Fuzzy matching must not fire on a generic alias like 'machine translation'."""
    datasets = [
        DatasetCandidate(
            name="SomeDataset",
            source="Hugging Face",
            aliases=["machine translation"],
        )
    ]

    evidence = [
        PaperEvidence(
            paper_title="NMT Survey",
            paper_url="https://arxiv.org/abs/1234.0003",
            evidence_sentence="We evaluate neural machine translation models.",
            score=3,
            source_text_type="abstract",
        )
    ]

    matches = match_datasets_with_evidence(datasets, evidence)

    assert len(matches) == 0


def test_exact_strong_alias_with_usage_context_matches():
    """Exact match on a specific multi-word alias with usage context should match."""
    datasets = [
        DatasetCandidate(
            name="GlobalPhone Vietnamese",
            source="European Language Grid",
            aliases=["GlobalPhone Vietnamese"],
        )
    ]

    evidence = [
        PaperEvidence(
            paper_title="Vietnamese ASR",
            paper_url="https://arxiv.org/abs/1234.0004",
            evidence_sentence="We train the ASR model on the GlobalPhone Vietnamese corpus.",
            score=5,
            source_text_type="full_text_pdf",
        )
    ]

    matches = match_datasets_with_evidence(datasets, evidence)

    assert len(matches) == 1


def test_dataset_name_not_matched_as_substring():
    """'INCLUDE' dataset must not match the word 'included' in a sentence."""
    datasets = [
        DatasetCandidate(
            name="INCLUDE",
            source="Hugging Face",
            aliases=["INCLUDE"],
        )
    ]

    evidence = [
        PaperEvidence(
            paper_title="Document Layout Analysis",
            paper_url="https://arxiv.org/abs/1234.0005",
            evidence_sentence=(
                "Above from left to right, are example documents sourced from the RVL-CDIP "
                "and DocLaynet datasets demonstrating the complex layout and domains included "
                "in the benchmark."
            ),
            score=3,
            source_text_type="full_text_pdf",
        )
    ]

    matches = match_datasets_with_evidence(datasets, evidence)

    assert len(matches) == 0
