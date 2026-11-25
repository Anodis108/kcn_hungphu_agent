"""Cache reset test helper."""

from __future__ import annotations

from src.infra.memory.ttl_cache import clear_ttl_cache


def reset_ttl_cache() -> None:
    """Reset in-memory TTL cache entries for isolated tests."""
    clear_ttl_cache()
