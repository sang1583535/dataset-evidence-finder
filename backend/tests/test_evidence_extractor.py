from app.models.schemas import PaperMetadata
from app.services.evidence_extractor import (
    contains_evidence_term,
    extract_dataset_like_names,
    extract_evidence_from_text,
    score_evidence_sentence,
    split_sentences,
)


def _paper() -> PaperMetadata:
    return PaperMetadata(
        arxiv_id="1234.5678",
        title="A Study",
        summary="Summary.",
        url="https://arxiv.org/abs/1234.5678",
        pdf_url="https://arxiv.org/pdf/1234.5678",
    )


def test_split_sentences_splits_on_punctuation():
    sentences = split_sentences("First sentence. Second sentence! Third?")
    assert sentences == ["First sentence.", "Second sentence!", "Third?"]


def test_contains_evidence_term():
    assert contains_evidence_term("We use the CoNLL dataset.")
    assert not contains_evidence_term("This is an unrelated sentence.")


def test_score_rewards_usage_and_penalizes_short():
    strong = score_evidence_sentence("We evaluate our model on the SQuAD dataset.")
    weak = score_evidence_sentence("A dataset.")
    assert strong > weak


def test_extract_dataset_like_names_filters_stopwords():
    names = extract_dataset_like_names("We use CoNLL-2003 and The data.")
    assert "CoNLL-2003" in names
    assert "The" not in names


def test_extract_evidence_from_text_returns_scored_items():
    text = (
        "We evaluate our system on the SQuAD dataset. "
        "This sentence has nothing relevant at all."
    )

    evidence = extract_evidence_from_text(
        paper=_paper(),
        text=text,
        source_text_type="abstract",
    )

    assert len(evidence) == 1
    assert evidence[0].source_text_type == "abstract"
    assert evidence[0].score > 0
