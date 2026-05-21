from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.import_persistence import (
    ImportPersistence,
    normalize_raw_rows,
)
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardDataRepository,
)
from tm_app.infrastructure.persistence.sheet_raw_loader import SheetRawLoader


@dataclass
class ImportValidation:
    ok: bool
    errors: list[str] = field(default_factory=list)
    sheet_counts: dict[str, int] = field(default_factory=dict)


class SheetImportService:
    def __init__(self) -> None:
        self._loader = SheetRawLoader()
        self._calculator = DashboardCalculatorService()

    def load(self, *, csv_dir: Path | None = None) -> TransformometroRawData:
        raw = self._loader.load(csv_dir=csv_dir)
        return normalize_raw_rows(raw)

    def validate(self, raw: TransformometroRawData) -> ImportValidation:
        errors: list[str] = []
        sheet_counts = {
            "processos": len(raw.processos),
            "revisoes": len(raw.revisoes),
            "medicoes": len(raw.medicoes),
            "investimentos": len(raw.investimentos),
            "recursos_compartilhados": len(raw.recursos_compartilhados),
            "vinculos": len(raw.revisao_recursos_compartilhados),
        }

        processo_ids = {p["processo_id"] for p in raw.processos}
        codigos = set()
        for row in raw.processos:
            if not row.get("nome_processo"):
                errors.append(f"Processo {row.get('processo_id')}: nome_processo obrigatório.")
            if not row.get("filial_id"):
                errors.append(f"Processo {row.get('processo_id')}: filial_id obrigatório.")
            codigo = row.get("codigo_processo")
            if codigo in codigos:
                errors.append(f"codigo_processo duplicado na planilha: {codigo}")
            codigos.add(codigo)

        revisao_ids = set()
        for row in raw.revisoes:
            rid = row.get("revisao_id")
            if rid in revisao_ids:
                errors.append(f"revisao_id duplicado: {rid}")
            revisao_ids.add(rid)
            if not row.get("processo_id"):
                errors.append(f"Revisão {rid}: processo_id inválido ou ausente.")
            elif row["processo_id"] not in processo_ids:
                errors.append(f"Revisão {rid}: processo_id não encontrado em processos.")
            if not row.get("data_inicio_vigencia"):
                errors.append(f"Revisão {rid}: data_inicio_vigencia obrigatória.")

        for row in raw.medicoes:
            if row.get("revisao_id") not in revisao_ids:
                errors.append(f"Medição: revisao_id {row.get('revisao_id')} não encontrado.")

        for row in raw.investimentos:
            if row.get("revisao_id") not in revisao_ids:
                errors.append(f"Investimento {row.get('investimento_id')}: revisao_id inválido.")

        recurso_ids = {r["recurso_compartilhado_id"] for r in raw.recursos_compartilhados}
        for row in raw.revisao_recursos_compartilhados:
            if row.get("revisao_id") not in revisao_ids:
                errors.append(f"Vínculo {row.get('vinculo_id')}: revisao_id inválido.")
            if row.get("recurso_compartilhado_id") not in recurso_ids:
                errors.append(
                    f"Vínculo {row.get('vinculo_id')}: recurso_compartilhado_id inválido."
                )

        return ImportValidation(ok=len(errors) == 0, errors=errors, sheet_counts=sheet_counts)

    def preview(self, *, csv_dir: Path | None = None) -> dict[str, Any]:
        raw = self.load(csv_dir=csv_dir)
        validation = self.validate(raw)
        sheet_summary = self._calculator.build_summary(raw, None, None, None)

        db_counts = self._db_counts()
        db_summary = None
        if db_counts.get("processos", 0) > 0:
            db_raw = DashboardDataRepository().load_raw()
            db_summary = self._calculator.build_summary(db_raw, None, None, None)

        return {
            "validation": {
                "ok": validation.ok,
                "errors": validation.errors,
                "sheet_counts": validation.sheet_counts,
            },
            "sheet_summary": _summary_slice(sheet_summary),
            "db_counts": db_counts,
            "db_summary": _summary_slice(db_summary) if db_summary else None,
        }

    def apply(
        self,
        *,
        csv_dir: Path | None = None,
        replace_existing: bool = False,
        recalc_dashboard: bool = True,
    ) -> dict[str, Any]:
        raw = self.load(csv_dir=csv_dir)
        validation = self.validate(raw)
        if not validation.ok:
            raise ValueError("; ".join(validation.errors[:20]))

        imported = ImportPersistence().import_all(raw, replace_existing=replace_existing)

        recalc = None
        if recalc_dashboard:
            recalc = DashboardRecalcService().recalculate()

        diff = self.diff_after_import(raw)

        return {
            "imported": imported,
            "recalc": recalc,
            "diff": diff,
            "validation": {"sheet_counts": validation.sheet_counts},
        }

    def diff_after_import(self, sheet_raw: TransformometroRawData) -> dict[str, Any]:
        sheet_summary = self._calculator.build_summary(sheet_raw, None, None, None)
        db_raw = DashboardDataRepository().load_raw()
        db_summary = self._calculator.build_summary(db_raw, None, None, None)

        metrics = [
            ("economia_liquida_total", "economia_liquida_total"),
            ("economia_bruta_total", "economia_bruta_total"),
            ("solucoes_implementadas", "solucoes_implementadas"),
        ]
        items = []
        for label, key in metrics:
            sheet_val = float(sheet_summary.get(key) or 0)
            db_val = float(db_summary.get(key) or 0)
            delta = round(db_val - sheet_val, 2)
            items.append(
                {
                    "metric": label,
                    "sheet": sheet_val,
                    "database": db_val,
                    "delta": delta,
                    "match": abs(delta) < 0.05,
                }
            )

        return {
            "items": items,
            "all_match": all(item["match"] for item in items),
        }

    def _db_counts(self) -> dict[str, int]:
        repo = ImportPersistence()
        counts: dict[str, int] = {}
        for key, table, has_deleted in [
            ("processos", "transformometro.processos", True),
            ("revisoes", "transformometro.revisoes", True),
            ("medicoes", "transformometro.medicoes", True),
            ("investimentos", "transformometro.investimentos", True),
            ("recursos", "transformometro.recursos_compartilhados", True),
            ("vinculos", "transformometro.revisao_recursos_compartilhados", True),
            ("dashboard_calculos", "transformometro.dashboard_calculos", False),
        ]:
            if has_deleted:
                sql = f"SELECT COUNT(*)::int AS c FROM {table} WHERE deletado = FALSE"
            else:
                sql = f"SELECT COUNT(*)::int AS c FROM {table}"
            row = repo.fetch_one(sql)
            counts[key] = int((row or {}).get("c") or 0)
        return counts


def _summary_slice(summary: dict | None) -> dict[str, Any] | None:
    if not summary:
        return None
    return {
        "solucoes_implementadas": summary.get("solucoes_implementadas"),
        "economia_liquida_total": summary.get("economia_liquida_total"),
        "economia_bruta_total": summary.get("economia_bruta_total"),
        "roi_medio": summary.get("roi_medio"),
    }
