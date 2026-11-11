"""Coletor Linux read-only de inventário automático (E4.S1)."""

from .diagnose import build_observation_payload, collect_host_snapshot

__all__ = ["build_observation_payload", "collect_host_snapshot"]
