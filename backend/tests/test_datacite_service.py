from app.services.datacite_service import search_datacite_datasets


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_search_datacite_parses_candidates(monkeypatch):
    payload = {
        "data": [
            {
                "attributes": {
                    "titles": [{"title": "Example Speech Corpus"}],
                    "doi": "10.1234/example",
                    "url": None,
                    "descriptions": [{"description": "A spoken corpus."}],
                    "subjects": [{"subject": "speech"}, {"subject": "nlp"}],
                }
            },
            {
                # Missing title -> skipped.
                "attributes": {"titles": []}
            },
        ]
    }

    monkeypatch.setattr(
        "app.services.datacite_service.requests.get",
        lambda *a, **k: _FakeResponse(payload),
    )

    results = search_datacite_datasets("speech", limit=5)

    assert len(results) == 1
    candidate = results[0]
    assert candidate.name == "Example Speech Corpus"
    assert candidate.source == "DataCite"
    assert candidate.url == "https://doi.org/10.1234/example"
    assert candidate.description == "A spoken corpus."
    assert candidate.tags == ["speech", "nlp"]


def test_search_datacite_handles_empty_data(monkeypatch):
    monkeypatch.setattr(
        "app.services.datacite_service.requests.get",
        lambda *a, **k: _FakeResponse({"data": []}),
    )

    assert search_datacite_datasets("nothing", limit=5) == []
