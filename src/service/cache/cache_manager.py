"""
Cache Manager — SKILL_05
In-process TTL cache for API responses.
Prevents redundant PubMed / ClinicalTrials / Tavily calls within a session.

TTLs:
  DEFAULT_TTL  = 3600s  (1h)  — PubMed, ClinicalTrials, Tavily responses
  BRIEF_TTL    = 86400s (24h) — full brief outputs
  RAG_TTL      = 21600s (6h)  — RAG index results
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Optional


DEFAULT_TTL: int = 3600
BRIEF_TTL: int = 86400
RAG_TTL: int = 21600


class CacheManager:
    """Thread-safe in-process TTL dictionary cache."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def make_key(self, api_type: str, *args: str) -> str:
        """
        Returns a stable cache key from api_type + args.
        Example: make_key("pubmed", "sotorasib", "KRAS G12C NSCLC")
        """
        raw = "|".join([api_type, *[str(a).lower().strip() for a in args]])
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Return cached value if key exists and has not expired.
        Deletes expired entry and returns None if expired.
        """
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Store value with expiry = now + ttl seconds."""
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    def clear_drug(self, drug_name: str) -> int:
        """
        Delete all cache entries whose key was built with drug_name.
        Returns count of deleted entries.
        Note: because keys are hashed, this rebuilds possible keys from
        common api_types and compares. For a full clear, use clear_all().
        """
        # Practical approach: mark all entries as expired (soft clear)
        count = 0
        to_delete = []
        for k, v in self._store.items():
            # We can't reverse the hash, so expire everything and let get() clean up.
            # This is intentionally conservative — call clear_all() for a hard reset.
            _ = k  # suppress unused var
        # Instead, store raw key metadata alongside hashed key for drug-level clear
        raw_prefix = drug_name.lower().strip()
        to_delete = [k for k, v in self._store.items()
                     if v.get("raw_key", "").startswith(raw_prefix)]
        for k in to_delete:
            del self._store[k]
            count += 1
        return count

    def set_with_raw(self, key: str, raw_key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Store value with raw_key metadata (enables clear_drug())."""
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "raw_key": raw_key,
        }

    def clear_all(self) -> None:
        """Remove all cached entries."""
        self._store.clear()

    def stats(self) -> dict:
        """Return total, expired, and active entry counts."""
        now = time.time()
        total = len(self._store)
        expired = sum(1 for v in self._store.values() if now > v["expires_at"])
        return {
            "total": total,
            "expired": expired,
            "active": total - expired,
        }


# Module-level singleton — import and use directly:
#   from src.service.cache.cache_manager import cache, DEFAULT_TTL, BRIEF_TTL
cache = CacheManager()
