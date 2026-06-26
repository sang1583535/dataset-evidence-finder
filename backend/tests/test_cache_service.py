import time

from app.services import cache_service
from app.services.cache_service import (
    make_cache_key,
    read_json_cache,
    write_json_cache,
)


def test_make_cache_key_is_deterministic():
    assert make_cache_key("a", "b") == make_cache_key("a", "b")
    assert make_cache_key("a", "b") != make_cache_key("b", "a")


def test_write_then_read_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_service, "CACHE_ROOT", tmp_path)

    data = {"value": 42, "items": [1, 2, 3]}
    write_json_cache("unit_ns", "key1", data)

    assert read_json_cache("unit_ns", "key1") == data


def test_read_missing_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_service, "CACHE_ROOT", tmp_path)

    assert read_json_cache("unit_ns", "does_not_exist") is None


def test_read_respects_ttl(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_service, "CACHE_ROOT", tmp_path)

    write_json_cache("unit_ns", "key_ttl", {"a": 1})

    # Fresh entry within TTL is returned.
    assert read_json_cache("unit_ns", "key_ttl", ttl_seconds=1000) == {"a": 1}

    # Pretend a lot of time has passed so the entry is expired.
    real_time = time.time()
    monkeypatch.setattr(cache_service.time, "time", lambda: real_time + 10_000)
    assert read_json_cache("unit_ns", "key_ttl", ttl_seconds=1) is None
