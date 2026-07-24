from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.core.catalogs import FILIAIS
from tm_app.core.serialize import rows_to_json
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.setor_catalog_service import normalize_codigo_setor
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.json_backup_repository import (
    BUNDLE_KEYS,
    ENTITY_SPECS,
    INSTANCIA_DECOMPOSICAO_ESCOPOS_BUNDLE_KEY,
    INSTANCIA_DIAGRAMA_ESCOPOS_BUNDLE_KEY,
    PROCESSO_ARQUIVOS_BUNDLE_KEY,
    PROCESSO_DECOMPOSICAO_BUNDLE_KEY,
    PROCESSO_DIAGRAMAS_BUNDLE_KEY,
    PROCESSO_FILIAIS_BUNDLE_KEY,
    PROCESSO_INSTANCIA_SETORES_BUNDLE_KEY,
    PROCESSO_SETORES_BUNDLE_KEY,
    REVISAO_DECOMPOSICAO_OVERLAYS_BUNDLE_KEY,
    REVISAO_DIAGRAMA_OVERLAYS_BUNDLE_KEY,
    REVISAO_EVIDENCIAS_BUNDLE_KEY,
    SETOR_FILIAIS_BUNDLE_KEY,
    EntitySpec,
    JsonBackupRepository,
)

ExportMode = Literal["replace", "merge"]
ImportFormat = Literal["auto", "modern", "legacy"]
ResolvedImportFormat = Literal["modern", "legacy"]
SCHEMA_VERSION = "1.4"
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION, "1.3", "1.2", "1.1", "1.0"})
LEGACY_IMPORT_NAMESPACE = NAMESPACE_DNS

IMPORT_FORMAT_INCOMPATIBLE_MESSAGE = (
    "Formato do arquivo não reconhecido ou incompatível com o Transformômetro. "
    "Envie um backup exportado por este app (legado 1.1 com unidade e setor nos processos, "
    "ou Playbook 18 com instâncias operacionais)."
)

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _norm_id(value: Any) -> str:
    return str(value).strip().lower()


def _is_uuid(value: Any) -> bool:
    text = str(value).strip()
    if not _UUID_PATTERN.match(text):
        return False
    try:
        UUID(text)
    except ValueError:
        return False
    return True


def _legacy_filial_id(codigo_filial: str) -> str:
    return str(uuid5(LEGACY_IMPORT_NAMESPACE, f"transformometro.filial:{codigo_filial}"))


def _legacy_setor_id(codigo_setor: str) -> str:
    return str(uuid5(LEGACY_IMPORT_NAMESPACE, f"transformometro.setor:{codigo_setor}"))


def _legacy_instancia_id(processo_id: str, codigo_filial: str) -> str:
    return str(
        uuid5(
            LEGACY_IMPORT_NAMESPACE,
            f"transformometro.instancia:{processo_id}:{codigo_filial}",
        )
    )


def _is_transformometro_backup(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False

    schema_version = payload.get("schema_version")
    if schema_version is not None and schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        return False

    markers = {
        "processos",
        "setores",
        "revisoes",
        "recursos_compartilhados",
        "processo_instancias",
        "filiais",
        "schema_version",
        "exported_at",
    }
    return bool(set(payload.keys()) & markers)


def detect_import_format(payload: dict[str, Any]) -> ResolvedImportFormat | None:
    """Classifica legado vs Playbook 18. None = formato não reconhecido (modo auto)."""
    if not _is_transformometro_backup(payload):
        return None

    instancias = [
        row for row in (payload.get("processo_instancias") or []) if isinstance(row, dict)
    ]
    if instancias:
        return "modern"

    processos = [row for row in (payload.get("processos") or []) if isinstance(row, dict)]
    if any(
        isinstance(row, dict) and row.get("filial_id") and row.get("setor_id")
        for row in processos
    ):
        return "legacy"

    revisoes_ativas = [
        row
        for row in (payload.get("revisoes") or [])
        if isinstance(row, dict) and not row.get("deletado")
    ]
    if revisoes_ativas and not instancias:
        if any(not row.get("instancia_id") for row in revisoes_ativas):
            return None

    if processos:
        if all(not (row.get("filial_id") and row.get("setor_id")) for row in processos):
            return "modern"

    setores = payload.get("setores") or []
    filiais = payload.get("filiais") or []
    if (setores or filiais) and not processos:
        return "modern"

    explicit = payload.get("import_format")
    if explicit in ("modern", "legacy"):
        return explicit

    return None


def _collect_filial_codigos(payload: dict[str, Any]) -> set[str]:
    codigos: set[str] = set()
    for row in payload.get("processos") or []:
        if isinstance(row, dict) and row.get("filial_id"):
            codigos.add(str(row["filial_id"]).strip())
    for row in payload.get("setor_filiais") or []:
        if isinstance(row, dict) and row.get("filial_id"):
            codigos.add(str(row["filial_id"]).strip())
    for row in payload.get("filiais") or []:
        if isinstance(row, dict):
            codigo = row.get("codigo_filial") or row.get("id")
            if codigo:
                codigos.add(str(codigo).strip())
    return {codigo for codigo in codigos if codigo}


def _setor_keys_in_row(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    setor_id = row.get("setor_id")
    if setor_id:
        keys.add(_norm_id(setor_id))
    codigo = row.get("codigo_setor")
    if codigo:
        keys.add(_norm_id(codigo))
    return keys


def _build_id_sets(payload: dict[str, Any]) -> dict[str, set[str]]:
    id_sets: dict[str, set[str]] = {}
    for spec in ENTITY_SPECS:
        keys: set[str] = set()
        for row in payload.get(spec.bundle_key, []):
            if not isinstance(row, dict):
                continue
            if spec.bundle_key == "setores":
                keys.update(_setor_keys_in_row(row))
            elif row.get(spec.pk):
                keys.add(_norm_id(row[spec.pk]))
        id_sets[spec.bundle_key] = keys
    return id_sets


def _as_dict(raw: TransformometroRawData) -> dict[str, list[dict[str, Any]]]:
    return {
        "processos": raw.processos,
        "processo_instancias": raw.processo_instancias,
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
        # Fontes canônicas (não o subset magro de load_raw / dashboard).
        data["filiais"] = self._repo.fetch_filiais()
        data["setores"] = self._repo.fetch_setores()
        data["setor_filiais"] = self._repo.fetch_setor_filiais()
        data["processos"] = self._repo.fetch_processos()
        data["processo_filiais"] = self._repo.fetch_processo_filiais()
        data["processo_setores"] = self._repo.fetch_processo_setores()
        data["processo_instancias"] = self._repo.fetch_processo_instancias()
        data["processo_instancia_setores"] = self._repo.fetch_processo_instancia_setores()
        data["processo_diagramas"] = self._repo.fetch_processo_diagramas()
        data["instancia_diagrama_escopos"] = self._repo.fetch_instancia_diagrama_escopos()
        data["revisao_diagrama_overlays"] = self._repo.fetch_revisao_diagrama_overlays()
        data["processo_decomposicao"] = self._repo.fetch_processo_decomposicao()
        data["instancia_decomposicao_escopos"] = self._repo.fetch_instancia_decomposicao_escopos()
        data["revisao_decomposicao_overlays"] = self._repo.fetch_revisao_decomposicao_overlays()
        data["revisao_evidencias"] = self._repo.fetch_revisao_evidencias()
        data["processo_arquivos"] = self._repo.fetch_processo_arquivos()
        data = self._repo.ensure_bundle_parent_rows(data)
        return {
            "schema_version": SCHEMA_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "import_format": "modern",
            "counts": {key: len(data.get(key) or []) for key in BUNDLE_KEYS},
            **{key: rows_to_json(data.get(key) or []) for key in BUNDLE_KEYS},
        }

    def resolve_import_payload(
        self,
        payload: dict[str, Any],
        import_format: ImportFormat = "auto",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        detected = detect_import_format(payload)
        requested = import_format
        if import_format == "auto":
            resolved: ResolvedImportFormat | None = detected
        else:
            resolved = import_format

        prepared = copy.deepcopy(payload)
        for key in BUNDLE_KEYS:
            if prepared.get(key) is None:
                prepared[key] = []

        legacy_transformed = False
        if resolved == "legacy":
            self._prepare_legacy_payload(prepared)
            legacy_transformed = True

        meta = {
            "requested_format": requested,
            "resolved_format": resolved,
            "detected_format": detected,
            "legacy_transformed": legacy_transformed,
            "format_compatible": resolved is not None
            if requested == "auto"
            else True,
        }
        return prepared, meta

    def validate_bundle(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []

        if payload.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
            errors.append(
                f"schema_version inválida (esperado {SCHEMA_VERSION!r} ou legado 1.1)."
            )

        for key in BUNDLE_KEYS:
            rows = payload.get(key)
            # Schemas antigos omitem chaves novas — tratar como lista vazia.
            if rows is None:
                rows = []
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

            if key in {PROCESSO_FILIAIS_BUNDLE_KEY, PROCESSO_SETORES_BUNDLE_KEY}:
                link_field = (
                    "filial_id" if key == PROCESSO_FILIAIS_BUNDLE_KEY else "setor_id"
                )
                seen_links: set[tuple[str, str]] = set()
                for index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        errors.append(f"{key}[{index}]: registro deve ser objeto.")
                        continue
                    processo_id = row.get("processo_id")
                    link_id = row.get(link_field) or row.get(
                        "codigo_filial" if link_field == "filial_id" else "codigo_setor"
                    )
                    if not processo_id:
                        errors.append(f"{key}[{index}]: processo_id obrigatório.")
                    if not link_id:
                        errors.append(f"{key}[{index}]: {link_field} obrigatório.")
                    if processo_id and link_id:
                        pair = (_norm_id(processo_id), str(link_id).strip().lower())
                        if pair in seen_links:
                            errors.append(
                                f"{key}: vínculo duplicado ({processo_id}, {link_id})."
                            )
                        seen_links.add(pair)
                continue

            if key == PROCESSO_INSTANCIA_SETORES_BUNDLE_KEY:
                seen_links: set[tuple[str, str]] = set()
                for index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        errors.append(f"{key}[{index}]: registro deve ser objeto.")
                        continue
                    instancia_id = row.get("instancia_id")
                    setor_id = row.get("setor_id")
                    if not instancia_id:
                        errors.append(f"{key}[{index}]: instancia_id obrigatório.")
                    if not setor_id:
                        errors.append(f"{key}[{index}]: setor_id obrigatório.")
                    if instancia_id and setor_id:
                        pair = (_norm_id(instancia_id), _norm_id(setor_id))
                        if pair in seen_links:
                            errors.append(
                                f"{key}: vínculo duplicado ({instancia_id}, {setor_id})."
                            )
                        seen_links.add(pair)
                continue

            if key in {
                PROCESSO_DIAGRAMAS_BUNDLE_KEY,
                INSTANCIA_DIAGRAMA_ESCOPOS_BUNDLE_KEY,
                REVISAO_DIAGRAMA_OVERLAYS_BUNDLE_KEY,
                PROCESSO_DECOMPOSICAO_BUNDLE_KEY,
                INSTANCIA_DECOMPOSICAO_ESCOPOS_BUNDLE_KEY,
                REVISAO_DECOMPOSICAO_OVERLAYS_BUNDLE_KEY,
            }:
                pk_field = {
                    PROCESSO_DIAGRAMAS_BUNDLE_KEY: "processo_id",
                    INSTANCIA_DIAGRAMA_ESCOPOS_BUNDLE_KEY: "instancia_id",
                    REVISAO_DIAGRAMA_OVERLAYS_BUNDLE_KEY: "revisao_id",
                    PROCESSO_DECOMPOSICAO_BUNDLE_KEY: "processo_id",
                    INSTANCIA_DECOMPOSICAO_ESCOPOS_BUNDLE_KEY: "instancia_id",
                    REVISAO_DECOMPOSICAO_OVERLAYS_BUNDLE_KEY: "revisao_id",
                }[key]
                seen_diagram: set[str] = set()
                for index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        errors.append(f"{key}[{index}]: registro deve ser objeto.")
                        continue
                    pk = row.get(pk_field)
                    if not pk:
                        errors.append(f"{key}[{index}]: {pk_field} obrigatório.")
                        continue
                    pk_str = _norm_id(pk)
                    if pk_str in seen_diagram:
                        errors.append(f"{key}: {pk_field} duplicado ({pk_str}).")
                    seen_diagram.add(pk_str)
                continue

            if key == REVISAO_EVIDENCIAS_BUNDLE_KEY:
                seen_evidence: set[str] = set()
                for index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        errors.append(f"{key}[{index}]: registro deve ser objeto.")
                        continue
                    evidencia_id = row.get("evidencia_id")
                    revisao_id = row.get("revisao_id")
                    if not evidencia_id:
                        errors.append(f"{key}[{index}]: evidencia_id obrigatório.")
                    if not revisao_id:
                        errors.append(f"{key}[{index}]: revisao_id obrigatório.")
                    if evidencia_id:
                        pk_str = _norm_id(evidencia_id)
                        if pk_str in seen_evidence:
                            errors.append(f"{key}: evidencia_id duplicado ({pk_str}).")
                        seen_evidence.add(pk_str)
                continue

            if key == PROCESSO_ARQUIVOS_BUNDLE_KEY:
                seen_arquivos: set[str] = set()
                for index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        errors.append(f"{key}[{index}]: registro deve ser objeto.")
                        continue
                    arquivo_id = row.get("arquivo_id")
                    processo_id = row.get("processo_id")
                    if not arquivo_id:
                        errors.append(f"{key}[{index}]: arquivo_id obrigatório.")
                    if not processo_id:
                        errors.append(f"{key}[{index}]: processo_id obrigatório.")
                    if arquivo_id:
                        pk_str = _norm_id(arquivo_id)
                        if pk_str in seen_arquivos:
                            errors.append(f"{key}: arquivo_id duplicado ({pk_str}).")
                        seen_arquivos.add(pk_str)
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
                row_keys = {_norm_id(pk)}
                if spec.bundle_key == "setores":
                    row_keys = _setor_keys_in_row(row)
                for pk_str in row_keys:
                    if pk_str in seen:
                        errors.append(f"{key}: {spec.pk} duplicado ({pk_str}).")
                    seen.add(pk_str)

        if errors:
            return _dedupe_errors(errors)

        errors.extend(self._validate_modern_requirements(payload))
        if errors:
            return _dedupe_errors(errors)

        id_sets = _build_id_sets(payload)

        for spec in ENTITY_SPECS:
            for row in payload.get(spec.bundle_key, []):
                if not isinstance(row, dict):
                    continue
                for fk_col, parent_key, _parent_pk in spec.fk_checks:
                    fk_val = row.get(fk_col)
                    if fk_val is None:
                        if (
                            spec.bundle_key == "processo_instancias"
                            and fk_col == "filial_id"
                            and bool(row.get("todas_filiais_ativas"))
                        ):
                            continue
                        errors.append(
                            f"{spec.bundle_key}: {fk_col} ausente em {row.get(spec.pk)}."
                        )
                        continue
                    parent_keys = id_sets.get(parent_key, set())
                    if _norm_id(fk_val) not in parent_keys:
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

        setor_keys = id_sets.get("setores", set())
        for row in payload.get("processos", []):
            if not isinstance(row, dict):
                continue
            setor_id = row.get("setor_id")
            if setor_id and _norm_id(setor_id) not in setor_keys:
                errors.append(
                    f"processos: setor_id={setor_id} não está em setores no JSON "
                    f"(reexporte o backup ou inclua o setor)."
                )

        processo_ids = id_sets.get("processos", set())
        instancia_ids = id_sets.get("processo_instancias", set())
        revisao_ids = id_sets.get("revisoes", set())

        for row in payload.get(PROCESSO_DIAGRAMAS_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("processo_id"):
                pid = _norm_id(row["processo_id"])
                if pid not in processo_ids:
                    errors.append(
                        f"processo_diagramas: processo_id={pid} não está em processos no JSON."
                    )

        for row in payload.get(INSTANCIA_DIAGRAMA_ESCOPOS_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("instancia_id"):
                iid = _norm_id(row["instancia_id"])
                if iid not in instancia_ids:
                    errors.append(
                        f"instancia_diagrama_escopos: instancia_id={iid} não está em processo_instancias no JSON."
                    )

        for row in payload.get(REVISAO_DIAGRAMA_OVERLAYS_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("revisao_id"):
                rid = _norm_id(row["revisao_id"])
                if rid not in revisao_ids:
                    errors.append(
                        f"revisao_diagrama_overlays: revisao_id={rid} não está em revisoes no JSON."
                    )

        for row in payload.get(PROCESSO_DECOMPOSICAO_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("processo_id"):
                pid = _norm_id(row["processo_id"])
                if pid not in processo_ids:
                    errors.append(
                        f"processo_decomposicao: processo_id={pid} não está em processos no JSON."
                    )

        for row in payload.get(INSTANCIA_DECOMPOSICAO_ESCOPOS_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("instancia_id"):
                iid = _norm_id(row["instancia_id"])
                if iid not in instancia_ids:
                    errors.append(
                        f"instancia_decomposicao_escopos: instancia_id={iid} não está em processo_instancias no JSON."
                    )

        for row in payload.get(REVISAO_DECOMPOSICAO_OVERLAYS_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("revisao_id"):
                rid = _norm_id(row["revisao_id"])
                if rid not in revisao_ids:
                    errors.append(
                        f"revisao_decomposicao_overlays: revisao_id={rid} não está em revisoes no JSON."
                    )

        for row in payload.get(REVISAO_EVIDENCIAS_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("revisao_id"):
                rid = _norm_id(row["revisao_id"])
                if rid not in revisao_ids:
                    errors.append(
                        f"revisao_evidencias: revisao_id={rid} não está em revisoes no JSON."
                    )

        for row in payload.get(PROCESSO_ARQUIVOS_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("processo_id"):
                pid = _norm_id(row["processo_id"])
                if pid not in processo_ids:
                    errors.append(
                        f"processo_arquivos: processo_id={pid} não está em processos no JSON."
                    )

        for row in payload.get(PROCESSO_FILIAIS_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("processo_id"):
                pid = _norm_id(row["processo_id"])
                if pid not in processo_ids:
                    errors.append(
                        f"processo_filiais: processo_id={pid} não está em processos no JSON."
                    )

        for row in payload.get(PROCESSO_SETORES_BUNDLE_KEY, []):
            if isinstance(row, dict) and row.get("processo_id"):
                pid = _norm_id(row["processo_id"])
                if pid not in processo_ids:
                    errors.append(
                        f"processo_setores: processo_id={pid} não está em processos no JSON."
                    )

        revisao_ids_all = id_sets.get("revisoes", set())
        for row in payload.get("revisoes", []):
            if not isinstance(row, dict):
                continue
            ref = row.get("revisao_referencia_id")
            if not ref:
                continue
            if _norm_id(ref) not in revisao_ids_all:
                errors.append(
                    f"revisoes: revisao_referencia_id={ref} não está em revisoes no JSON."
                )

        return _dedupe_errors(errors)

    def preview(
        self,
        payload: dict[str, Any],
        mode: ExportMode,
        import_format: ImportFormat = "auto",
    ) -> dict[str, Any]:
        detected = detect_import_format(payload)
        if import_format == "auto" and detected is None:
            return {
                "valid": False,
                "errors": [IMPORT_FORMAT_INCOMPATIBLE_MESSAGE],
                "mode": mode,
                "entities": {},
                "requested_format": import_format,
                "detected_format": None,
                "resolved_format": None,
                "legacy_transformed": False,
                "format_compatible": False,
            }

        prepared, format_meta = self.resolve_import_payload(payload, import_format)
        if format_meta.get("resolved_format") is None:
            return {
                "valid": False,
                "errors": [IMPORT_FORMAT_INCOMPATIBLE_MESSAGE],
                "mode": mode,
                "entities": {},
                **format_meta,
                "format_compatible": False,
            }

        errors = self.validate_bundle(prepared)
        if errors:
            return {
                "valid": False,
                "errors": errors,
                "mode": mode,
                "entities": {},
                **format_meta,
            }

        if format_meta["resolved_format"] == "modern" and format_meta["requested_format"] == "modern":
            raw_errors = self.validate_bundle(payload)
            if raw_errors:
                return {
                    "valid": False,
                    "errors": [
                        *raw_errors,
                        "Pacote parece legado (sem instâncias/revisões por instância). "
                        "Use import_format=legacy ou auto.",
                    ],
                    "mode": mode,
                    "entities": {},
                    **format_meta,
                }

        existing = {spec.bundle_key: self._repo.fetch_existing_ids(spec) for spec in ENTITY_SPECS}
        entities: dict[str, dict[str, int]] = {}

        for spec in ENTITY_SPECS:
            rows = prepared.get(spec.bundle_key, [])
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

        evidence_rows = prepared.get(REVISAO_EVIDENCIAS_BUNDLE_KEY, [])
        evidence_existing = self._repo.fetch_revisao_evidencias_existing_ids()
        ev_insert = ev_update = ev_skip = 0
        for row in evidence_rows:
            if not isinstance(row, dict):
                continue
            pk = str(row.get("evidencia_id", ""))
            if not pk:
                ev_skip += 1
                continue
            if mode == "merge":
                if pk in evidence_existing:
                    ev_update += 1
                else:
                    ev_insert += 1
            else:
                ev_insert += 1
        entities[REVISAO_EVIDENCIAS_BUNDLE_KEY] = {
            "total": len(evidence_rows),
            "insert": ev_insert,
            "update": ev_update,
            "skip": ev_skip,
        }

        arquivo_rows = prepared.get(PROCESSO_ARQUIVOS_BUNDLE_KEY, [])
        arquivo_existing = self._repo.fetch_processo_arquivos_existing_ids()
        arq_insert = arq_update = arq_skip = 0
        for row in arquivo_rows:
            if not isinstance(row, dict):
                continue
            pk = str(row.get("arquivo_id", ""))
            if not pk:
                arq_skip += 1
                continue
            if mode == "merge":
                if pk in arquivo_existing:
                    arq_update += 1
                else:
                    arq_insert += 1
            else:
                arq_insert += 1
        entities[PROCESSO_ARQUIVOS_BUNDLE_KEY] = {
            "total": len(arquivo_rows),
            "insert": arq_insert,
            "update": arq_update,
            "skip": arq_skip,
        }

        sf_rows = prepared.get(SETOR_FILIAIS_BUNDLE_KEY, [])
        entities[SETOR_FILIAIS_BUNDLE_KEY] = {
            "total": len(sf_rows),
            "insert": len(sf_rows),
            "update": 0,
            "skip": 0,
        }
        for link_key in (PROCESSO_FILIAIS_BUNDLE_KEY, PROCESSO_SETORES_BUNDLE_KEY):
            link_rows = prepared.get(link_key, [])
            entities[link_key] = {
                "total": len(link_rows),
                "insert": len(link_rows),
                "update": 0,
                "skip": 0,
            }

        if mode == "replace":
            current_counts = self._current_bundle_counts()
        else:
            current_counts = {key: len(existing.get(key, set())) for key in BUNDLE_KEYS}
            current_counts[SETOR_FILIAIS_BUNDLE_KEY] = len(self._repo.fetch_setor_filiais())
            current_counts[PROCESSO_FILIAIS_BUNDLE_KEY] = len(
                self._repo.fetch_processo_filiais()
            )
            current_counts[PROCESSO_SETORES_BUNDLE_KEY] = len(
                self._repo.fetch_processo_setores()
            )

        return {
            "valid": True,
            "errors": [],
            "mode": mode,
            "entities": entities,
            "current_counts": current_counts,
            "import_counts": {key: len(prepared.get(key, [])) for key in BUNDLE_KEYS},
            **format_meta,
        }

    def apply(
        self,
        payload: dict[str, Any],
        mode: ExportMode,
        import_format: ImportFormat = "auto",
    ) -> dict[str, Any]:
        preview = self.preview(payload, mode, import_format)
        if not preview.get("valid"):
            raise ValueError("; ".join(preview.get("errors") or ["Pacote inválido."]))

        prepared, _format_meta = self.resolve_import_payload(payload, import_format)

        try:
            if mode == "replace":
                self._repo.truncate_cadastral_tables()
                for spec in ENTITY_SPECS:
                    for row in prepared.get(spec.bundle_key, []):
                        if isinstance(row, dict):
                            self._repo.insert_row(
                                spec, self._normalize_row(spec, row), auto_commit=False
                            )
            else:
                for spec in ENTITY_SPECS:
                    for row in prepared.get(spec.bundle_key, []):
                        if isinstance(row, dict):
                            self._repo.upsert_row(
                                spec, self._normalize_row(spec, row), auto_commit=False
                            )

            sf_rows = [
                row
                for row in prepared.get(SETOR_FILIAIS_BUNDLE_KEY, [])
                if isinstance(row, dict)
            ]
            self._repo.sync_setor_filiais(sf_rows, auto_commit=False)
            self._repo.sync_processo_escopo_links(prepared, auto_commit=False)
            self._sync_processo_instancias_from_payload(prepared)
            self._sync_processo_instancia_setores_from_payload(prepared)
            self._repo.sync_diagram_bundles(prepared, auto_commit=False)
            self._repo.sync_decomposition_bundles(prepared, auto_commit=False)
            self._repo.sync_revisao_evidencias(prepared, auto_commit=False)
            self._repo.sync_processo_arquivos(prepared, auto_commit=False)

            self._repo._connection.commit()
        except Exception:
            self._repo._connection.rollback()
            raise

        recalc = DashboardRecalcService().recalculate()
        return {
            "mode": mode,
            "entities": preview["entities"],
            "recalc": recalc,
            "requested_format": preview.get("requested_format"),
            "resolved_format": preview.get("resolved_format"),
            "detected_format": preview.get("detected_format"),
            "legacy_transformed": preview.get("legacy_transformed"),
        }

    def _validate_modern_requirements(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        instancias = payload.get("processo_instancias") or []
        revisoes = [row for row in (payload.get("revisoes") or []) if isinstance(row, dict)]
        if revisoes and not instancias:
            errors.append(
                "processo_instancias: obrigatório quando há revisões (use import_format=legacy)."
            )
        for row in revisoes:
            if row.get("instancia_id"):
                continue
            if not self._revisao_requires_instancia_id(row, payload):
                continue
            errors.append(
                f"revisoes: instancia_id ausente em {row.get('revisao_id')} "
                f"(use import_format=legacy ou reexporte o backup)."
            )
        return errors

    @staticmethod
    def _revisao_requires_instancia_id(revisao: dict[str, Any], payload: dict[str, Any]) -> bool:
        processo_id = str(revisao.get("processo_id") or "")
        if not processo_id:
            return True
        processos = {
            str(row.get("processo_id")): row
            for row in (payload.get("processos") or [])
            if isinstance(row, dict) and row.get("processo_id")
        }
        processo = processos.get(processo_id)
        if processo and processo.get("deletado"):
            return False
        instancias = [
            row
            for row in (payload.get("processo_instancias") or [])
            if isinstance(row, dict)
            and str(row.get("processo_id") or "") == processo_id
            and not row.get("deletado")
        ]
        return bool(instancias)

    def _prepare_legacy_payload(self, payload: dict[str, Any]) -> None:
        labels: dict[str, str] = dict(FILIAIS)
        for row in payload.get("filiais") or []:
            if not isinstance(row, dict):
                continue
            codigo = str(row.get("codigo_filial") or row.get("id") or "").strip()
            nome = str(row.get("nome_filial") or row.get("label") or "").strip()
            if codigo and nome:
                labels[codigo] = nome

        filiais = [
            row for row in (payload.get("filiais") or []) if isinstance(row, dict)
        ]
        filiais_by_codigo = {
            str(row.get("codigo_filial") or "").strip(): row
            for row in filiais
            if row.get("codigo_filial")
        }

        for codigo in sorted(_collect_filial_codigos(payload)):
            if codigo in filiais_by_codigo:
                row = filiais_by_codigo[codigo]
                if not row.get("filial_id"):
                    row["filial_id"] = _legacy_filial_id(codigo)
                continue
            filial_row = {
                "filial_id": _legacy_filial_id(codigo),
                "codigo_filial": codigo,
                "nome_filial": labels.get(codigo, f"Unidade {codigo}"),
                "status_filial": "ativo",
                "deletado": False,
            }
            filiais.append(filial_row)
            filiais_by_codigo[codigo] = filial_row
        payload["filiais"] = filiais

        setor_codigo_to_uuid: dict[str, str] = {}
        for row in payload.get("setores") or []:
            if not isinstance(row, dict):
                continue
            codigo = normalize_codigo_setor(
                str(row.get("codigo_setor") or row.get("setor_id") or "")
            )
            if not codigo:
                continue
            if _is_uuid(str(row.get("setor_id") or "")):
                setor_uuid = str(row["setor_id"])
            else:
                setor_uuid = _legacy_setor_id(codigo)
            row["codigo_setor"] = codigo
            row["setor_id"] = setor_uuid
            setor_codigo_to_uuid[codigo] = setor_uuid
            setor_codigo_to_uuid[_norm_id(codigo)] = setor_uuid

        filial_codigo_to_uuid = {
            str(row["codigo_filial"]).strip(): str(row["filial_id"])
            for row in payload["filiais"]
            if row.get("codigo_filial") and row.get("filial_id")
        }

        instancias = [
            row
            for row in (payload.get("processo_instancias") or [])
            if isinstance(row, dict)
        ]
        links = [
            row
            for row in (payload.get("processo_instancia_setores") or [])
            if isinstance(row, dict)
        ]
        inst_by_processo: dict[str, str] = {}
        inst_by_processo_filial: dict[tuple[str, str], str] = {}

        for processo in payload.get("processos") or []:
            if not isinstance(processo, dict):
                continue
            processo_id = str(processo.get("processo_id") or "")
            filial_codigo = str(processo.get("filial_id") or "").strip()
            setor_raw = str(processo.get("setor_id") or "").strip()
            if not processo_id or not filial_codigo or not setor_raw:
                continue
            setor_codigo = normalize_codigo_setor(setor_raw)
            filial_uuid = filial_codigo_to_uuid.get(filial_codigo)
            setor_uuid = setor_codigo_to_uuid.get(setor_codigo) or setor_codigo_to_uuid.get(
                _norm_id(setor_codigo)
            )
            if not filial_uuid or not setor_uuid:
                continue

            key = (processo_id, filial_codigo)
            instancia_id = inst_by_processo_filial.get(key)
            if not instancia_id:
                instancia_id = _legacy_instancia_id(processo_id, filial_codigo)
                instancias.append(
                    {
                        "instancia_id": instancia_id,
                        "processo_id": processo_id,
                        "filial_id": filial_uuid,
                        "todas_filiais_ativas": False,
                        "status_instancia": "ativo",
                        "deletado": False,
                    }
                )
                inst_by_processo_filial[key] = instancia_id
            links.append(
                {
                    "instancia_id": instancia_id,
                    "setor_id": setor_uuid,
                }
            )
            inst_by_processo.setdefault(processo_id, instancia_id)

        payload["processo_instancias"] = instancias
        payload["processo_instancia_setores"] = links

        for revisao in payload.get("revisoes") or []:
            if not isinstance(revisao, dict) or revisao.get("instancia_id"):
                continue
            processo_id = str(revisao.get("processo_id") or "")
            instancia_id = inst_by_processo.get(processo_id)
            if not instancia_id:
                continue
            revisao["instancia_id"] = instancia_id
            versao = revisao.get("versao_revisao") or ""
            revisao["chave_unica_processo_revisao"] = f"{instancia_id}|{versao}"

    def _current_bundle_counts(self) -> dict[str, int]:
        raw = self._repo.load_export_bundle()
        data = _as_dict(raw)
        skip_keys = {
            SETOR_FILIAIS_BUNDLE_KEY,
            PROCESSO_FILIAIS_BUNDLE_KEY,
            PROCESSO_SETORES_BUNDLE_KEY,
            PROCESSO_INSTANCIA_SETORES_BUNDLE_KEY,
            REVISAO_EVIDENCIAS_BUNDLE_KEY,
            PROCESSO_ARQUIVOS_BUNDLE_KEY,
            "processos",
            "processo_instancias",
        }
        return {
            **{
                key: len(data.get(key) or [])
                for key in BUNDLE_KEYS
                if key not in skip_keys
            },
            "filiais": len(self._repo.fetch_filiais()),
            "setores": len(self._repo.fetch_setores()),
            "processos": len(self._repo.fetch_processos()),
            "processo_instancias": len(self._repo.fetch_processo_instancias()),
            SETOR_FILIAIS_BUNDLE_KEY: len(self._repo.fetch_setor_filiais()),
            PROCESSO_FILIAIS_BUNDLE_KEY: len(self._repo.fetch_processo_filiais()),
            PROCESSO_SETORES_BUNDLE_KEY: len(self._repo.fetch_processo_setores()),
            PROCESSO_INSTANCIA_SETORES_BUNDLE_KEY: len(
                self._repo.fetch_processo_instancia_setores()
            ),
            REVISAO_EVIDENCIAS_BUNDLE_KEY: len(self._repo.fetch_revisao_evidencias()),
            PROCESSO_ARQUIVOS_BUNDLE_KEY: len(self._repo.fetch_processo_arquivos()),
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
        if spec.bundle_key == "processo_instancias" and not out.get("status_instancia"):
            out["status_instancia"] = "ativo"
        if spec.bundle_key == "recursos_compartilhados" and "escopo_recurso" not in out:
            out["escopo_recurso"] = "empresa"
        if spec.bundle_key == "revisoes" and out.get("chave_unica_processo_revisao") is None:
            instancia_id = out.get("instancia_id")
            if instancia_id:
                out["chave_unica_processo_revisao"] = (
                    f"{instancia_id}|{out.get('versao_revisao')}"
                )
            else:
                out["chave_unica_processo_revisao"] = (
                    f"{out.get('processo_id')}|{out.get('versao_revisao')}"
                )
        if spec.bundle_key == "setores":
            raw_id = row.get("setor_id")
            codigo = row.get("codigo_setor")
            if codigo:
                out["codigo_setor"] = normalize_codigo_setor(str(codigo))
            elif raw_id is not None and not _is_uuid(raw_id):
                out["codigo_setor"] = normalize_codigo_setor(str(raw_id))
            if raw_id is not None and _is_uuid(raw_id):
                out["setor_id"] = str(raw_id)
            else:
                if "codigo_setor" in out:
                    out["setor_id"] = _legacy_setor_id(out["codigo_setor"])
                else:
                    out["setor_id"] = str(uuid4())
                if "codigo_setor" not in out and raw_id is not None:
                    out["codigo_setor"] = normalize_codigo_setor(str(raw_id))
        return out

    def _sync_processo_instancias_from_payload(self, payload: dict[str, Any]) -> None:
        inst_repo = ProcessoInstanciaRepository(connection=self._repo._connection)
        links = [
            row
            for row in (payload.get("processo_instancia_setores") or [])
            if isinstance(row, dict)
        ]
        setores_by_instancia: dict[str, list[str]] = {}
        for row in links:
            instancia_id = str(row.get("instancia_id") or "")
            setor_id = str(row.get("setor_id") or "")
            if instancia_id and setor_id:
                setores_by_instancia.setdefault(instancia_id, []).append(setor_id)

        for row in payload.get("processo_instancias") or []:
            if not isinstance(row, dict):
                continue
            processo_id = row.get("processo_id")
            filial_id = row.get("filial_id")
            todas_filiais = bool(row.get("todas_filiais_ativas"))
            instancia_id = str(row.get("instancia_id") or "")
            setor_ids = [
                str(item)
                for item in (row.get("setor_ids") or [])
                if str(item).strip()
            ]
            if not setor_ids and instancia_id:
                setor_ids = setores_by_instancia.get(instancia_id, [])
            legacy_setor = row.get("setor_id")
            if legacy_setor:
                setor_ids.append(str(legacy_setor))
            setor_ids = list(dict.fromkeys(setor_ids))
            if not processo_id or not setor_ids:
                continue
            if not todas_filiais and not filial_id:
                continue
            try:
                created = inst_repo.create(
                    {
                        "processo_id": str(processo_id),
                        "filial_id": str(filial_id) if filial_id else None,
                        "todas_filiais_ativas": todas_filiais,
                        "setor_ids": setor_ids,
                        "rotulo_instancia": row.get("rotulo_instancia"),
                        "status_instancia": row.get("status_instancia") or "ativo",
                        "resumo_melhoria": row.get("resumo_melhoria"),
                        "responsavel_local": row.get("responsavel_local"),
                        "fase_melhoria": row.get("fase_melhoria"),
                        "data_alvo_go_live": row.get("data_alvo_go_live"),
                        "prioridade": row.get("prioridade"),
                    },
                    auto_commit=False,
                )
                contexto = row.get("contexto")
                if isinstance(contexto, dict) and created.get("instancia_id"):
                    inst_repo.update_contexto(
                        str(created["instancia_id"]), contexto, auto_commit=False
                    )
            except Exception:
                existing = inst_repo.get_by_processo(str(processo_id))
                if existing is None:
                    raise

    def _sync_processo_instancia_setores_from_payload(self, payload: dict[str, Any]) -> None:
        for row in payload.get("processo_instancia_setores") or []:
            if not isinstance(row, dict):
                continue
            instancia_id = row.get("instancia_id")
            setor_id = row.get("setor_id")
            if not instancia_id or not setor_id:
                continue
            self._repo.execute(
                """
                INSERT INTO transformometro.processo_instancia_setores (instancia_id, setor_id)
                VALUES (%s::uuid, %s::uuid)
                ON CONFLICT (instancia_id, setor_id) DO NOTHING
                """,
                (str(instancia_id), str(setor_id)),
                auto_commit=False,
            )


def _dedupe_errors(errors: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for message in errors:
        if message in seen:
            continue
        seen.add(message)
        unique.append(message)
    return unique
