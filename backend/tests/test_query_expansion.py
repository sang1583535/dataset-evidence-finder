import pytest

from app.models.schemas import DatasetCandidate
from app.services.query_expansion import (
    build_alias_paper_queries,
    choose_best_alias,
    is_good_alias,
)


def _candidate(name: str, aliases: list[str]) -> DatasetCandidate:
    return DatasetCandidate(name=name, source="Test", aliases=aliases)


# --- is_good_alias ---

def test_accepts_globalphone_vietnamese():
    assert is_good_alias("GlobalPhone Vietnamese") is True


def test_rejects_too_short():
    assert is_good_alias("QA") is False
    assert is_good_alias("en") is False
    assert is_good_alias("") is False


def test_rejects_generic_single_word():
    for term in ("dataset", "corpus", "data", "text", "nlp", "benchmark"):
        assert is_good_alias(term) is False, f"Expected {term!r} to be rejected"


def test_rejects_all_generic_multiword():
    assert is_good_alias("nlp dataset") is False
    assert is_good_alias("speech corpus") is False


def test_rejects_too_many_words():
    assert is_good_alias("this is a very long alias with too many words") is False


def test_accepts_meaningful_aliases():
    assert is_good_alias("MAP-CC") is True
    assert is_good_alias("VIVOS") is True
    assert is_good_alias("Common Voice Vietnamese") is True
    assert is_good_alias("SST-2") is True


# --- choose_best_alias ---

def test_prefers_short_name_after_slash():
    c = _candidate("m-a-p/MAP-CC", ["m-a-p/MAP-CC", "MAP-CC", "m-a-p MAP-CC"])
    assert choose_best_alias(c) == "MAP-CC"


def test_returns_none_when_all_generic():
    c = _candidate("dataset", ["dataset", "corpus", "text data"])
    assert choose_best_alias(c) is None


def test_returns_good_alias_from_list():
    c = _candidate("dataset", ["dataset", "VIVOS corpus", "VIVOS"])
    result = choose_best_alias(c)
    assert result is not None
    assert is_good_alias(result)


# --- build_alias_paper_queries ---

def test_user_query_is_always_first():
    candidates = [_candidate("VIVOS", ["VIVOS"])]
    queries = build_alias_paper_queries("Vietnamese speech", candidates)
    assert queries[0] == "Vietnamese speech"


def test_deduplicates_aliases():
    candidates = [
        _candidate("VIVOS", ["VIVOS"]),
        _candidate("vivos-corpus", ["VIVOS", "vivos corpus"]),
    ]
    queries = build_alias_paper_queries("Vietnamese speech", candidates, max_alias_queries=5)
    normalized = [q.lower() for q in queries]
    assert normalized.count("vivos") == 1


def test_respects_max_alias_queries():
    candidates = [_candidate(f"Dataset{i}", [f"Alias{i}"]) for i in range(10)]
    queries = build_alias_paper_queries("some query", candidates, max_alias_queries=3)
    assert len(queries) <= 4  # original + 3


def test_skips_generic_candidates():
    candidates = [
        _candidate("dataset", ["dataset", "corpus"]),
        _candidate("GlobalPhone Vietnamese", ["GlobalPhone Vietnamese"]),
    ]
    queries = build_alias_paper_queries("Vietnamese speech", candidates, max_alias_queries=3)
    assert "GlobalPhone Vietnamese" in queries
    assert "dataset" not in queries
    assert "corpus" not in queries


def test_user_query_not_duplicated_as_alias():
    candidates = [_candidate("Vietnamese speech", ["Vietnamese speech"])]
    queries = build_alias_paper_queries("Vietnamese speech", candidates, max_alias_queries=3)
    assert queries.count("Vietnamese speech") == 1
