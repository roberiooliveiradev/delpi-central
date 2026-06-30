from __future__ import annotations

from pathlib import Path

import pytest

from app.application.services.quality_action_plans.pac_evidence_storage import (
    PacEvidenceStorage,
    PacEvidenceStorageError,
)


def test_resolve_evidence_file_finds_uuid_folder_when_path_uses_plan_code(tmp_path: Path) -> None:
    plan_uuid = "f0e274de-cc4b-4b68-b9cb-881408f9374b"
    stored_name = "abc123.xlsx"
    target = tmp_path / plan_uuid / stored_name
    target.parent.mkdir(parents=True)
    target.write_bytes(b"planilha")

    storage = PacEvidenceStorage(base_dir=str(tmp_path))
    resolved = storage.resolve_evidence_file(
        stored_name=stored_name,
        plan_id_candidates=storage.plan_id_candidates(
            plan_ref="PAC-2026-0002",
            evidence={"plan_id": plan_uuid},
        ),
    )

    assert resolved == target.resolve()


def test_resolve_evidence_file_legacy_code_folder(tmp_path: Path) -> None:
    stored_name = "legacy.xlsx"
    legacy_dir = tmp_path / "PAC-2026-0002"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / stored_name).write_bytes(b"legacy")

    storage = PacEvidenceStorage(base_dir=str(tmp_path))
    resolved = storage.resolve_evidence_file(
        stored_name=stored_name,
        plan_id_candidates=storage.plan_id_candidates(
            plan_ref="PAC-2026-0002",
            evidence={"plan_id": "uuid-1"},
        ),
    )

    assert resolved.name == stored_name


def test_resolve_evidence_file_missing_raises(tmp_path: Path) -> None:
    storage = PacEvidenceStorage(base_dir=str(tmp_path))
    with pytest.raises(PacEvidenceStorageError, match="Arquivo não encontrado"):
        storage.resolve_evidence_file(
            stored_name="missing.xlsx",
            plan_id_candidates=["PAC-2026-0002"],
        )
