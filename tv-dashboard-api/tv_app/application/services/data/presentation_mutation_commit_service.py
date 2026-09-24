"""Editor / VISTA shared commit: PresentationMutation → persist nativeConfig.

The patch reducer is pure (httpCommands for GPT). The MFE editor needs an
ack path that applies ops and writes via ``TvPresentationWriteService`` so
backend-owned geometry/style/defaults become the single source of truth.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    TvPresentationWriteService,
)


class PresentationMutationCommitService:
    """Apply TvPresentationPatchV1 ops and persist the resulting slide config."""

    def __init__(
        self,
        *,
        patch: PresentationPatchService | None = None,
        writes: TvPresentationWriteService | None = None,
    ) -> None:
        self._patch = patch or PresentationPatchService()
        self._writes = writes or TvPresentationWriteService()

    def commit(
        self,
        *,
        playlist_id: UUID | str,
        slide_id: UUID | str,
        ops: list[dict[str, Any]],
        user: Any,
        actor_user_id: str,
        authorization: str | None = None,
        expected_revision: int | None = None,
        base_native_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run ops against the slide and persist ``nativeConfig``.

        When ``base_native_config`` is provided (editor draft), the reducer
        still loads from DB via target ids; for pure editor drafts that already
        match DB, ops patch the loaded config. To support local-ahead drafts,
        callers should prefer upserting the full block state via ``upsert_block``
        ops rather than replacing the whole config client-side.
        """
        del base_native_config  # reserved — authority is DB + ops
        envelope = {
            "version": "TvPresentationPatchV1",
            "target": {
                "playlistId": str(playlist_id),
                "slideId": str(slide_id),
            },
            "ops": ops,
        }
        try:
            preview = self._patch.preview(
                envelope,
                user=user,
                authorization=authorization,
                include_fingerprint=True,
            )
        except PresentationPatchError:
            raise

        native_config = preview.get("nativeConfig")
        if not isinstance(native_config, dict):
            raise PresentationPatchError("Mutation não produziu nativeConfig.")

        try:
            slide = self._writes.update_slide(
                UUID(str(playlist_id)),
                UUID(str(slide_id)),
                {"nativeConfig": native_config},
                actor_user_id=actor_user_id,
                user=user,
                expected_revision=expected_revision,
            )
        except PresentationWriteError:
            raise

        return {
            "slide": slide,
            "nativeConfig": slide.get("nativeConfig")
            if isinstance(slide.get("nativeConfig"), dict)
            else native_config,
            "appliedOps": preview.get("appliedOps") or [],
            "fingerprint": preview.get("fingerprint"),
            "sideEffectHints": preview.get("sideEffectHints") or [],
            "persisted": True,
            "executionMode": "editor_mutation_commit",
            "message": preview.get("message") or "Mutação aplicada.",
        }
