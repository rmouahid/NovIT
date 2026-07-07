import time

from src.mcp.cache import TTLCache


def test_set_and_get():
    cache = TTLCache()
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_expiry():
    cache = TTLCache()
    cache.set("key", "value", ttl=1)
    time.sleep(1.1)
    assert cache.get("key") is None


def test_miss_increments_counter():
    cache = TTLCache()
    cache.get("missing")
    stats = cache.stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0


def test_hit_increments_counter():
    cache = TTLCache()
    cache.set("k", "v")
    cache.get("k")
    stats = cache.stats()
    assert stats["hits"] == 1


def test_delete():
    cache = TTLCache()
    cache.set("k", "v")
    cache.delete("k")
    assert cache.get("k") is None


def test_clear():
    cache = TTLCache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None
    assert cache.stats()["entries"] == 0


def test_hit_rate():
    cache = TTLCache()
    cache.set("k", "v")
    cache.get("k")  # hit
    cache.get("miss")  # miss
    stats = cache.stats()
    assert stats["hit_rate"] == 0.5


def test_entries_count():
    cache = TTLCache()
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.stats()["entries"] == 2


def test_overwrite_key():
    cache = TTLCache()
    cache.set("k", "v1")
    cache.set("k", "v2")
    assert cache.get("k") == "v2"
