"""Shared execution slots/aliases for presentation compound plans (preview + ACT)."""

from __future__ import annotations

import copy
import itertools
import uuid
from dataclasses import dataclass, field
from typing import Any

SYN_PREFIX = "syn:"


def is_synthetic_id(value: str | None) -> bool:
    return str(value or "").startswith(SYN_PREFIX)


def mint_synthetic_id(kind: str) -> str:
    token = uuid.uuid4().hex[:12]
    return f"{SYN_PREFIX}{kind}:{token}"


@dataclass
class ExecutionContext:
    """Mutable workspace for ordered op execution."""

    playlist_id: str | None = None
    slide_id: str | None = None
    section_id: str | None = None
    aliases: dict[str, str] = field(default_factory=dict)
    native_config: dict[str, Any] | None = None
    native_by_slide: dict[str, dict[str, Any]] = field(default_factory=dict)
    touched_native_slides: set[str] = field(default_factory=set)
    created: dict[str, Any] = field(default_factory=dict)
    _syn_counter: itertools.count = field(
        default_factory=lambda: itertools.count(1), repr=False
    )

    @classmethod
    def from_target(cls, target: dict[str, Any] | None) -> ExecutionContext:
        target_obj = target if isinstance(target, dict) else {}
        return cls(
            playlist_id=str(target_obj.get("playlistId") or "").strip() or None,
            slide_id=str(target_obj.get("slideId") or "").strip() or None,
            section_id=str(target_obj.get("sectionId") or "").strip() or None,
        )

    def resolve_playlist_id(self, op: dict[str, Any]) -> str | None:
        ref = str(op.get("playlistRef") or "").strip()
        if ref:
            return self.aliases.get(ref, ref)
        return self.playlist_id

    def resolve_slide_id(self, op: dict[str, Any]) -> str | None:
        ref = str(op.get("slideRef") or "").strip()
        if ref:
            return self.aliases.get(ref, ref)
        return self.slide_id

    def resolve_section_id(self, op: dict[str, Any]) -> str | None:
        ref = str(op.get("sectionRef") or "").strip()
        if ref:
            return self.aliases.get(ref, ref)
        return self.section_id

    def bind_alias(self, op: dict[str, Any], resource_id: str) -> None:
        alias = str(op.get("as") or "").strip()
        if alias and resource_id:
            self.aliases[alias] = resource_id

    def set_playlist(self, playlist_id: str, *, op: dict[str, Any] | None = None) -> None:
        self.playlist_id = playlist_id
        self.created["playlistId"] = playlist_id
        if op:
            self.bind_alias(op, playlist_id)

    def set_slide(
        self,
        slide_id: str,
        *,
        op: dict[str, Any] | None = None,
        native_config: dict[str, Any] | None = None,
    ) -> None:
        if self.slide_id and isinstance(self.native_config, dict):
            self.native_by_slide[str(self.slide_id)] = self.native_config
        self.slide_id = slide_id
        self.created["slideId"] = slide_id
        if native_config is not None:
            self.native_config = copy.deepcopy(native_config)
            self.native_by_slide[str(slide_id)] = self.native_config
            self.mark_native_touched(slide_id)
        elif str(slide_id) in self.native_by_slide:
            self.native_config = self.native_by_slide[str(slide_id)]
        if op:
            self.bind_alias(op, slide_id)

    def stash_native(self) -> None:
        if self.slide_id and isinstance(self.native_config, dict):
            self.native_by_slide[str(self.slide_id)] = self.native_config

    def activate_native(self, slide_id: str, native_config: dict[str, Any]) -> dict[str, Any]:
        self.stash_native()
        self.slide_id = slide_id
        self.native_config = native_config
        self.native_by_slide[str(slide_id)] = native_config
        self.mark_native_touched(slide_id)
        return native_config

    def mark_native_touched(self, slide_id: str | None) -> None:
        sid = str(slide_id or "").strip()
        if sid:
            self.touched_native_slides.add(sid)

    def set_section(self, section_id: str, *, op: dict[str, Any] | None = None) -> None:
        self.section_id = section_id
        self.created["sectionId"] = section_id
        if op:
            self.bind_alias(op, section_id)

    def ensure_native_config(self) -> dict[str, Any]:
        if not isinstance(self.native_config, dict):
            self.native_config = {
                "version": 5,
                "headline": "",
                "subtitle": "",
                "blocks": [],
            }
        if self.slide_id:
            self.native_by_slide[str(self.slide_id)] = self.native_config
            self.mark_native_touched(self.slide_id)
        return self.native_config

    def alias_map_public(self) -> dict[str, str]:
        return dict(self.aliases)

    def target_snapshot(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.playlist_id:
            out["playlistId"] = self.playlist_id
        if self.slide_id:
            out["slideId"] = self.slide_id
        if self.section_id:
            out["sectionId"] = self.section_id
        return out
