from app.services.match_filter import (
    allow_fuzzy_for_alias,
    has_dataset_usage_context,
    has_strong_usage_phrase,
    is_dataset_like_alias,
    is_generic_alias,
    is_valid_dataset_evidence,
)


def test_is_generic_alias():
    assert is_generic_alias("machine translation")
    assert not is_generic_alias("FLORES-200")


def test_is_dataset_like_alias():
    assert is_dataset_like_alias("FLORES-200")
    assert is_dataset_like_alias("XNLI")
    assert not is_dataset_like_alias("machine translation")


def test_allow_fuzzy_for_alias():
    assert allow_fuzzy_for_alias("CoNLL-2003")
    assert allow_fuzzy_for_alias("VIVOS")
    assert not allow_fuzzy_for_alias("translation")


def test_usage_phrase_helpers():
    assert has_strong_usage_phrase("We use the corpus for training.")
    assert not has_strong_usage_phrase("The corpus is large.")
    assert has_dataset_usage_context("We evaluate on the benchmark dataset.")
    assert not has_dataset_usage_context("This is a parallel corpus.")


def test_is_valid_dataset_evidence_by_match_type():
    assert is_valid_dataset_evidence(
        "We evaluate on the SQuAD dataset.", "SQuAD", "exact_alias_match"
    )
    assert is_valid_dataset_evidence(
        "We use FLORES-200 for evaluation.", "FLORES-200", "fuzzy_alias_match"
    )
    assert not is_valid_dataset_evidence(
        "We use FLORES-200 for evaluation.", "FLORES-200", "unknown_match"
    )
