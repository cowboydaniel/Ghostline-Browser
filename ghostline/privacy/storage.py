"""Partitioned storage primitives for cookies and caches."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PartitionedStore:
    """In-memory representation of partitioned cookie/cache state."""

    buckets: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def bucket_for(self, site: str, container: str = "default") -> Dict[str, str]:
        key = f"{site}:{container}"
        if key not in self.buckets:
            self.buckets[key] = {}
        return self.buckets[key]

    def set(self, site: str, name: str, value: str, container: str = "default") -> None:
        bucket = self.bucket_for(site, container)
        bucket[name] = value

    def get(self, site: str, name: str, container: str = "default") -> str | None:
        bucket = self.bucket_for(site, container)
        return bucket.get(name)

    def clear_container(self, container: str) -> None:
        keys_to_delete = [key for key in self.buckets if key.endswith(f":{container}")]
        for key in keys_to_delete:
            del self.buckets[key]
