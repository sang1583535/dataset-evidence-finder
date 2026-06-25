from app.models.schemas import SearchRequest


def test_search_request_accepts_optional_source_flags():
    request = SearchRequest(
        query="machine translation",
        use_openml=True,
        use_elg=False,
    )

    assert request.use_openml is True
    assert request.use_elg is False
