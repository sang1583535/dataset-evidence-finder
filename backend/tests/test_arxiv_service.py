from app.services.arxiv_service import search_arxiv_papers


def test_search_arxiv_papers_returns_empty_on_429(monkeypatch):
    class FakeResponse:
        status_code = 429
        text = ""

        def raise_for_status(self):
            raise AssertionError("raise_for_status should not be called for 429 fallback")

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("app.services.arxiv_service.requests.get", fake_get)

    papers = search_arxiv_papers("machine translation", max_results=3)

    assert papers == []
