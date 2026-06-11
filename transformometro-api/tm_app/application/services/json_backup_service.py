from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.core.serialize import rows_to_json
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.infrastructure.persistence.json_backup_repository import (
    BUNDLE_KEYS,
    ENTITY_SPECS,
    SETOR_FILIAIS_BUNDLE_KEY,
    EntitySpec,
    JsonBackupRepository,
)

ExportMode = Literal["replace", "merge"]
SCHEMA_VERSION = "1.1"


def _norm_id(value: Any) -> str:
    return str(value).strip().lower()


def _as_dict(raw: TransformometroRawData) -> dict[str, list[dict[str, Any]]]:
    return {
        "processos": raw.processos,
        "revisoes": raw.revisoes,
        "medicoes": raw.medicoes,
        "investimentos": raw.investimentos,
        "recursos_compartilhados": raw.recursos_compartilhados,
        "revisao_recursos_compartilhados": raw.revisao_recursos_compartilhados,
        "recurso_custos": raw.recurso_custos,
    }


def _entity_spec_for_key(key: str) -> EntitySpec:
    return next(spec for spec in ENTITY_SPECS if spec.bundle_key == key)


class JsonBackupService:
    def __init__(self, repo: JsonBackupRepository | None = None) -> None:
        self._repo = repo or JsonBackupRepository()

    def export_bundle(self) -> dict[str, Any]:
        raw = self._repo.load_export_bundle()
        data = self._repo.ensure_bundle_parent_rows(_as_dict(raw))
        data["setores"] = self._repo.fetch_setores()
        data["setor_filiais"] = self._repo.fetch_setor_filiais()
        data = self._repo.ensure_bundle_parent_rows(data)
        return {
            "schema_version": SCHEMA_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "counts": {key: len(data.get(key) or []) for key in BUNDLE_KEYS},
            **{key: rows_to_json(data.get(key) or []) for key in BUNDLE_KEYS},
        }

    def validate_bundle(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []

        if payload.get("schema_version") != SCHEMA_VERSION:
            errors.append(
                f"schema_version inválida (esperado {SCHEMA_VERSION!r})."
            )

        for key in BUNDLE_KEYS:
            rows = payload.get(key)
            if rows is None:
                errors.append(f"Campo obrigatório ausente: {key}.")
                continue
            if not isinstance(rows, list):
                errors.append(f"{key} deve ser uma lista.")
                continue

            if key == SETOR_FILIAIS_BUNDLE_KEY:
                seen_pairs: set[tuple[str, str]] = set()
                for index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        errors.append(f"{key}[{index}]: registro deve ser objeto.")
                        continue
                    setor_id = row.get("setor_id")
                    filial_id = row.get("filial_id")
                    if not setor_id:
                        errors.append(f"{key}[{index}]: setor_id obrigatório.")
                    if not filial_id:
                        errors.append(f"{key}[{index}]: filial_id obrigatório.")
                    if setor_id and filial_id:
                        pair = (_norm_id(setor_id), str(filial_id).strip())
                        if pair in seen_pairs:
                            errors.append(
                                f"{key}: vínculo duplicado ({setor_id}, {filial_id})."
                            )
                        seen_pairs.add(pair)
                continue

            spec = _entity_spec_for_key(key)
            seen: set[str] = set()
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    errors.append(f"{key}[{index}]: registro deve ser objeto.")
                    continue
                pk = row.get(spec.pk)
                if not pk:
                    errors.append(f"{key}[{index}]: {spec.pk} obrigatório.")
                    continue
                pk_str = _norm_id(pk)
                if pk_str in seen:
                    errors.append(f"{key}: {spec.pk} duplicado ({pk_str}).")
                seen.add(pk_str)

        if errors:
            return _dedupe_errors(errors)

        id_sets = {
            spec.bundle_key: {
                _norm_id(row[spec.pk])
                for row in payload.get(spec.bundle_key, [])
                if isinstance(row, dict) and row.get(spec.pk)
            }
            for spec in ENTITY_SPECS
        }

        for spec in ENTITY_SPECS:
            for row in payload.get(spec.bundle_key, []):
                if not isinstance(row, dict):
                    continue
                for fk_col, parent_key, _parent_pk in spec.fk_checks:
                    fk_val = row.get(fk_col)
                    if fk_val is None:
                        errors.append(
                            f"{spec.bundle_key}: {fk_col} ausente em {row.get(spec.pk)}."
                        )
                        continue
                    if _norm_id(fk_val) not in id_sets.get(parent_key, set()):
                        errors.append(
                            f"{spec.bundle_key}: {fk_col}={fk_val} não está em {parent_key} "
                            f"no JSON (reexporte o backup ou inclua o registro pai)."
                        )

        setor_ids = id_sets.get("setores", set())
        for row in payload.get(SETOR_FILIAIS_BUNDLE_KEY, []):
            if not isinstance(row, dict):
                continue
            setor_id = row.get("setor_id")
            if setor_id and _norm_id(setor_id) not in setor_ids:
                errors.append(
                    f"setor_filiais: setor_id={setor_id} não está em setores no JSON."
                )

        return _dedupe_errors(errors)

    def preview(self, payload: dict[str, Any], mode: ExportMode) -> dict[str, Any]:
        errors = self.validate_bundle(payload)
        if errors:
            return {"valid": False, "errors": errors, "mode": mode, "entities": {}}

        existing = {spec.bundle_key: self._repo.fetch_existing_ids(spec) for spec in ENTITY_SPECS}
        entities: dict[str, dict[str, int]] = {}

        for spec in ENTITY_SPECS:
            rows = payload.get(spec.bundle_key, [])
            insert = update = skip = 0
            for row in rows:
                if not isinstance(row, dict):
                    continue
                pk = str(row.get(spec.pk, ""))
                if not pk:
                    skip += 1
                    continue
                if mode == "merge":
                    if pk in existing[spec.bundle_key]:
                        update += 1
                    else:
                        insert += 1
                else:
                    insert += 1
            entities[spec.bundle_key] = {
                "total": len(rows),
                "insert": insert,
                "update": update,
                "skip": skip,
            }

        sf_rows = payload.get(SETOR_FILIAIS_BUNDLE_KEY, [])
        entities[SETOR_FILIAIS_BUNDLE_KEY] = {
            "total": len(sf_rows),
            "insert": len(sf_rows),
            "update": 0,
            "skip": 0,
        }

        if mode == "replace":
            current_counts = self._current_bundle_counts()
        else:
            current_counts = {key: len(existing.get(key, set())) for key in BUNDLE_KEYS}
            current_counts[SETOR_FILIAIS_BUNDLE_KEY] = len(self._repo.fetch_setor_filiais())

        return {
            "valid": True,
            "errors": [],
            "mode": mode,
            "entities": entities,
            "current_counts": current_counts,
            "import_counts": {key: len(payload.get(key, [])) for key in BUNDLE_KEYS},
        }

    def apply(self, payload: dict[str, Any], mode: ExportMode) -> dict[str, Any]:
        preview = self.preview(payload, mode)
        if not preview.get("valid"):
            raise ValueError("; ".join(preview.get("errors") or ["Pacote inválido."]))

        try:
            if mode == "replace":
                self._repo.truncate_cadastral_tables()
                for spec in ENTITY_SPECS:
                    for row in payload.get(spec.bundle_key, []):
                        if isinstance(row, dict):
                            self._repo.insert_row(spec, self._normalize_row(spec, row), auto_commit=False)
            else:
                for spec in ENTITY_SPECS:
                    for row in payload.get(spec.bundle_key, []):
                        if isinstance(row, dict):
                            self._repo.upsert_row(spec, self._normalize_row(spec, row), auto_commit=False)

            sf_rows = [
                row for row in payload.get(SETOR_FILIAIS_BUNDLE_KEY, []) if isinstance(row, dict)
            ]
            self._repo.sync_setor_filiais(sf_rows, auto_commit=False)

            self._repo._connection.commit()
        except Exception:
            self._repo._connection.rollback()
            raise

        recalc = DashboardRecalcService().recalculate()
        return {
            "mode": mode,
            "entities": preview["entities"],
            "recalc": recalc,
        }

    def _current_bundle_counts(self) -> dict[str, int]:
        raw = self._repo.load_export_bundle()
        data = _as_dict(raw)
        return {
            **{key: len(data.get(key) or []) for key in BUNDLE_KEYS if key != SETOR_FILIAIS_BUNDLE_KEY},
            "setores": len(self._repo.fetch_setores()),
            SETOR_FILIAIS_BUNDLE_KEY: len(self._repo.fetch_setor_filiais()),
        }

    @staticmethod
    def _normalize_row(spec: EntitySpec, row: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for col in spec.columns:
            if col not in row:
                continue
            value = row[col]
            if isinstance(value, UUID):
                value = str(value)
            out[col] = value
        if "deletado" not in out:
            out["deletado"] = False
        if spec.bundle_key == "revisoes" and out.get("chave_unica_processo_revisao") is None:
            out["chave_unica_processo_revisao"] = (
                f"{out.get('processo_id')}|{out.get('versao_revisao')}"
            )
        return out


def _dedupe_errors(errors: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for message in errors:
        if message in seen:
            continue
        seen.add(message)
        unique.append(message)
    return unique
