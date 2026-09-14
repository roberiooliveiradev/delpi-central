"""Guided improvement package — dry_run validation + orchestrated commit.

Reuses GptActionsDispatchService create/update/activate/recalculate paths
so RBAC and domain rules stay single-sourced.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.core.catalogs import CENARIO_TIPO


_UI_NEXT_STEPS = [
    "Optional: complete process diagram / WBS scope in Minha DELPI UI.",
    "Optional: attach evidence files on the revision in the UI.",
    "Optional: meeting minutes and handwritten signatures stay in the UI.",
    "Use gpt_analyze (view=summary|instances) to review KPIs after recalculate.",
]


class GuidedImprovementPackageService:
    def __init__(self, dispatch: GptActionsDispatchService | None = None) -> None:
        self._dispatch = dispatch or GptActionsDispatchService()

    def commit(self, request: Request, payload: dict[str, Any]) -> dict[str, Any]:
        body = dict(payload or {})
        dry_run = bool(body.get("dry_run", False))
        activate_scenario = bool(body.get("activate_scenario", False))
        recalculate = bool(body.get("recalculate", False))

        missing = self._collect_missing(body)
        checklist = self._checklist(body, missing)

        if dry_run:
            return {
                "dry_run": True,
                "ready": len(missing) == 0,
                "missing": missing,
                "checklist": checklist,
                "hints": {
                    "activate_scenario": activate_scenario,
                    "recalculate": recalculate,
                },
            }

        if missing:
            raise GptActionsError(
                "Improvement package incomplete. Fix missing fields or call with dry_run=true.",
                400,
                {"missing": missing, "checklist": checklist},
            )

        result: dict[str, Any] = {
            "dry_run": False,
            "created": {},
            "updated": {},
            "steps": [],
        }

        processo_id, process_action = self._resolve_process(request, body.get("process") or {})
        result["steps"].append({"step": "process", "action": process_action, "id": processo_id})
        result[process_action]["process"] = {"processo_id": processo_id}

        instancia_id, instance_action = self._resolve_instance(
            request, processo_id, body.get("instance") or {}
        )
        result["steps"].append(
            {"step": "instance", "action": instance_action, "id": instancia_id}
        )
        result[instance_action]["instance"] = {"instancia_id": instancia_id}

        baseline_block = body.get("baseline")
        baseline_revisao_id: str | None = None
        if isinstance(baseline_block, dict) and baseline_block:
            baseline_revisao_id, baseline_action = self._resolve_revision_block(
                request,
                processo_id=processo_id,
                instancia_id=instancia_id,
                block=baseline_block,
                force_cenario="baseline",
                allow_reference=False,
            )
            result["steps"].append(
                {
                    "step": "baseline",
                    "action": baseline_action,
                    "id": baseline_revisao_id,
                }
            )
            result.setdefault(baseline_action, {})["baseline_revision"] = {
                "revisao_id": baseline_revisao_id
            }

        scenario_block = body.get("scenario")
        scenario_revisao_id: str | None = None
        if isinstance(scenario_block, dict) and scenario_block:
            scenario_rev = dict(scenario_block.get("revision") or {})
            if not (scenario_rev.get("revisao_referencia_id") or "").strip():
                if baseline_revisao_id:
                    scenario_rev["revisao_referencia_id"] = baseline_revisao_id
                scenario_block = {**scenario_block, "revision": scenario_rev}
            scenario_revisao_id, scenario_action = self._resolve_revision_block(
                request,
                processo_id=processo_id,
                instancia_id=instancia_id,
                block=scenario_block,
                force_cenario=None,
                allow_reference=True,
            )
            result["steps"].append(
                {
                    "step": "scenario",
                    "action": scenario_action,
                    "id": scenario_revisao_id,
                }
            )
            result.setdefault(scenario_action, {})["scenario_revision"] = {
                "revisao_id": scenario_revisao_id
            }

        activated = None
        if activate_scenario:
            if not scenario_revisao_id:
                raise GptActionsError(
                    "activate_scenario=true requires a scenario revision.", 400
                )
            activated = self._dispatch.activate_revision(request, scenario_revisao_id)
            result["steps"].append(
                {"step": "activate", "action": "activated", "id": scenario_revisao_id}
            )
            result["activated"] = activated

        recalc_result = None
        if recalculate:
            recalc_result = self._dispatch.recalculate_dashboard(
                request,
                processo_id=processo_id,
                revisao_id=scenario_revisao_id or baseline_revisao_id,
            )
            result["steps"].append({"step": "recalculate", "action": "done"})
            result["recalculate"] = recalc_result

        result["ids"] = {
            "processo_id": processo_id,
            "instancia_id": instancia_id,
            "baseline_revisao_id": baseline_revisao_id,
            "scenario_revisao_id": scenario_revisao_id,
        }
        result["next_steps"] = list(_UI_NEXT_STEPS)
        return result

    def _collect_missing(self, body: dict[str, Any]) -> list[str]:
        missing: list[str] = []
        process = body.get("process") or {}
        instance = body.get("instance") or {}
        baseline = body.get("baseline")
        scenario = body.get("scenario")

        if not isinstance(process, dict) or not process:
            missing.append("process")
        elif not (process.get("id") or process.get("processo_id")):
            if not (process.get("nome_processo") or "").strip():
                missing.append("process.nome_processo")
            if not (process.get("status_processo") or "").strip():
                missing.append("process.status_processo")

        if not isinstance(instance, dict) or not instance:
            missing.append("instance")
        elif not (instance.get("id") or instance.get("instancia_id")):
            setor_ids = instance.get("setor_ids") or []
            if instance.get("setor_id") and not setor_ids:
                setor_ids = [instance.get("setor_id")]
            if not setor_ids:
                missing.append("instance.setor_ids")
            if not instance.get("todas_filiais_ativas") and not (
                instance.get("filial_id") or ""
            ).strip():
                missing.append("instance.filial_id_or_todas_filiais_ativas")

        has_baseline = isinstance(baseline, dict) and bool(baseline)
        has_scenario = isinstance(scenario, dict) and bool(scenario)
        if not has_baseline and not has_scenario:
            missing.append("baseline_or_scenario")

        if has_baseline:
            missing.extend(
                self._missing_revision_block(baseline, prefix="baseline", require_reference=False)
            )

        if has_scenario:
            missing.extend(
                self._missing_revision_block(scenario, prefix="scenario", require_reference=False)
            )
            scen_tipo = str(
                ((scenario.get("revision") or {}).get("cenario_tipo") or "")
            ).strip().lower()
            if scen_tipo == "baseline":
                missing.append("scenario.revision.cenario_tipo_must_not_be_baseline")
            elif scen_tipo and scen_tipo not in CENARIO_TIPO:
                missing.append("scenario.revision.cenario_tipo")
            ref = str(
                ((scenario.get("revision") or {}).get("revisao_referencia_id") or "")
            ).strip()
            scenario_has_id = bool(
                ((scenario.get("revision") or {}).get("id") or "")
                or ((scenario.get("revision") or {}).get("revisao_id") or "")
            )
            if not scenario_has_id and not ref and not has_baseline:
                missing.append("scenario.revision.revisao_referencia_id")

        if body.get("activate_scenario") and not has_scenario:
            missing.append("activate_scenario_requires_scenario")

        return missing

    def _missing_revision_block(
        self, block: dict[str, Any], *, prefix: str, require_reference: bool
    ) -> list[str]:
        missing: list[str] = []
        rev = block.get("revision") or {}
        if not isinstance(rev, dict) or not rev:
            missing.append(f"{prefix}.revision")
            return missing
        if rev.get("id") or rev.get("revisao_id"):
            return missing
        for field in ("versao_revisao", "cenario_tipo", "data_inicio_vigencia"):
            if prefix == "baseline" and field == "cenario_tipo":
                continue
            value = rev.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(f"{prefix}.revision.{field}")
        if require_reference:
            ref = rev.get("revisao_referencia_id")
            if ref is None or (isinstance(ref, str) and not ref.strip()):
                missing.append(f"{prefix}.revision.revisao_referencia_id")
        measurement = block.get("measurement")
        if measurement is not None and not isinstance(measurement, dict):
            missing.append(f"{prefix}.measurement")
        return missing

    def _checklist(self, body: dict[str, Any], missing: list[str]) -> list[dict[str, Any]]:
        items = [
            {"id": "process", "ok": "process" not in missing and not any(
                m.startswith("process.") for m in missing
            )},
            {"id": "instance", "ok": "instance" not in missing and not any(
                m.startswith("instance.") for m in missing
            )},
            {
                "id": "baseline",
                "ok": not any(m.startswith("baseline") for m in missing)
                or not (body.get("baseline")),
            },
            {
                "id": "scenario",
                "ok": not any(m.startswith("scenario") for m in missing)
                or not (body.get("scenario")),
            },
        ]
        return items

    def _resolve_process(
        self, request: Request, process: dict[str, Any]
    ) -> tuple[str, str]:
        pid = str(process.get("id") or process.get("processo_id") or "").strip()
        if pid:
            extra = {
                k: v
                for k, v in process.items()
                if k not in {"id", "processo_id"} and v is not None
            }
            if extra and any(
                k in extra
                for k in (
                    "nome_processo",
                    "status_processo",
                    "descricao_processo",
                    "gestor_responsavel",
                    "objetivo_processo",
                    "familia_processo",
                    "agrupador_ferramenta",
                )
            ):
                # update requires nome+status; fill from get if missing
                current = self._dispatch.get_record(request, "process", pid)
                data = {
                    "nome_processo": extra.get("nome_processo") or current.get("nome_processo"),
                    "status_processo": extra.get("status_processo")
                    or current.get("status_processo"),
                    **{
                        k: v
                        for k, v in extra.items()
                        if k not in {"nome_processo", "status_processo"}
                    },
                }
                self._dispatch.update_record(request, "process", pid, {"data": data})
                return pid, "updated"
            return pid, "reused"

        data = {k: v for k, v in process.items() if k not in {"id", "processo_id"}}
        # Package always creates/reuses instance separately — avoid dual create via process shortcut.
        data.pop("filial_id", None)
        data.pop("setor_id", None)
        row, _msg, _status = self._dispatch.create_record(
            request, "process", {"data": data}
        )
        return str(row["processo_id"]), "created"

    def _resolve_instance(
        self, request: Request, processo_id: str, instance: dict[str, Any]
    ) -> tuple[str, str]:
        iid = str(instance.get("id") or instance.get("instancia_id") or "").strip()
        if iid:
            extra = {
                k: v
                for k, v in instance.items()
                if k not in {"id", "instancia_id", "processo_id"} and v is not None
            }
            if extra and any(
                k in extra
                for k in (
                    "resumo_melhoria",
                    "fase_melhoria",
                    "prioridade",
                    "setor_ids",
                    "rotulo_instancia",
                    "responsavel_local",
                    "status_instancia",
                    "data_alvo_go_live",
                    "filial_id",
                    "todas_filiais_ativas",
                )
            ):
                current = self._dispatch.get_record(request, "instance", iid)
                data = {
                    "setor_ids": extra.get("setor_ids")
                    or current.get("setor_ids")
                    or ([current.get("setor_id")] if current.get("setor_id") else []),
                    "status_instancia": extra.get("status_instancia")
                    or current.get("status_instancia")
                    or "ativo",
                    **{
                        k: v
                        for k, v in extra.items()
                        if k not in {"setor_ids", "status_instancia"}
                    },
                }
                self._dispatch.update_record(request, "instance", iid, {"data": data})
                return iid, "updated"
            return iid, "reused"

        data = {
            k: v
            for k, v in instance.items()
            if k not in {"id", "instancia_id"}
        }
        data["processo_id"] = processo_id
        row, _msg, _status = self._dispatch.create_record(
            request, "instance", {"data": data}
        )
        return str(row["instancia_id"]), "created"

    def _resolve_revision_block(
        self,
        request: Request,
        *,
        processo_id: str,
        instancia_id: str,
        block: dict[str, Any],
        force_cenario: str | None,
        allow_reference: bool,
    ) -> tuple[str, str]:
        rev = dict(block.get("revision") or {})
        rid = str(rev.get("id") or rev.get("revisao_id") or "").strip()
        if force_cenario:
            rev["cenario_tipo"] = force_cenario
            rev.pop("revisao_referencia_id", None)
        if not allow_reference and rev.get("revisao_referencia_id"):
            rev.pop("revisao_referencia_id", None)

        if rid:
            extra = {
                k: v
                for k, v in rev.items()
                if k not in {"id", "revisao_id"} and v is not None
            }
            if extra:
                current = self._dispatch.get_record(request, "revision", rid)
                data = {
                    "processo_id": current.get("processo_id") or processo_id,
                    "instancia_id": current.get("instancia_id") or instancia_id,
                    "versao_revisao": extra.get("versao_revisao")
                    or current.get("versao_revisao"),
                    "cenario_tipo": extra.get("cenario_tipo") or current.get("cenario_tipo"),
                    "data_inicio_vigencia": extra.get("data_inicio_vigencia")
                    or current.get("data_inicio_vigencia"),
                    **{
                        k: v
                        for k, v in extra.items()
                        if k
                        not in {
                            "processo_id",
                            "instancia_id",
                            "versao_revisao",
                            "cenario_tipo",
                            "data_inicio_vigencia",
                        }
                    },
                }
                if force_cenario:
                    data["cenario_tipo"] = force_cenario
                self._dispatch.update_record(request, "revision", rid, {"data": data})
            action = "updated"
        else:
            data = {
                k: v
                for k, v in rev.items()
                if k not in {"id", "revisao_id"}
            }
            data["processo_id"] = processo_id
            data["instancia_id"] = instancia_id
            data.setdefault("revisao_ativa", False)
            if force_cenario:
                data["cenario_tipo"] = force_cenario
            row, _msg, _status = self._dispatch.create_record(
                request, "revision", {"data": data}
            )
            rid = str(row["revisao_id"])
            action = "created"

        measurement = block.get("measurement")
        if isinstance(measurement, dict):
            mdata = {k: v for k, v in measurement.items() if k != "revisao_id"}
            mdata["revisao_id"] = rid
            self._dispatch.create_record(request, "measurement", {"data": mdata})

        investments = block.get("investments") or []
        if isinstance(investments, list):
            for inv in investments:
                if not isinstance(inv, dict):
                    continue
                idata = {k: v for k, v in inv.items() if k != "revisao_id"}
                idata["revisao_id"] = rid
                self._dispatch.create_record(request, "investment", {"data": idata})

        return rid, action
