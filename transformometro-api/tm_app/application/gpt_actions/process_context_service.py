"""Ephemeral Process Intelligence Context for Custom GPT (read-only projection).

Assembles a semantic Process Business Graph from authoritative Transformômetro
records and existing application services. No graph persistence.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from tm_app.application.gpt_actions.dispatch_service import GptActionsError
from tm_app.application.services.decomposition_composition_service import (
    DecomposicaoCompositionService,
)
from tm_app.application.services.diagram_composition_service import (
    DiagramaCompositionService,
)
from tm_app.application.services.process_revision_compare_service import (
    ProcessRevisionCompareService,
)
from tm_app.application.services.process_setup_stats_service import (
    ProcessoSetupStatsService,
)
from tm_app.application.services.revision_impact_effort_matrix_service import (
    RevisaoImpactEffortMatrixService,
)
from tm_app.core.serialize import row_to_json, rows_to_json
from tm_app.interface.http.branch_access_http import (
    check_instancia_view_access,
    check_processo_view_access,
    filter_rows_for_access,
    require_transformometro_view_access,
)
from tm_app.infrastructure.persistence.repositories.investment_repository import (
    InvestimentoRepository,
)
from tm_app.infrastructure.persistence.repositories.measurement_repository import (
    MedicaoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_decomposition_repository import (
    ProcessoDecomposicaoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.infrastructure.persistence.repositories.process_instance_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (
    RevisaoRepository,
)
from tm_app.infrastructure.persistence.repositories.shared_resource_repository import (
    VinculoRepository,
)

CONTEXT_VERSION = "process_intelligence_context_v1"


class ProcessContextService:
    """Read-only aggregated process context for GPT Actions."""

    def get_context(
        self,
        request: Request,
        *,
        process_id: str,
        instance_id: str | None = None,
        revision_id: str | None = None,
    ) -> dict[str, Any]:
        self._raise(require_transformometro_view_access(request))
        processo_id = str(process_id or "").strip()
        if not processo_id:
            raise GptActionsError("process_id is required.", 400)

        self._raise(check_processo_view_access(request, processo_id))

        processo = ProcessoRepository().get(processo_id)
        if not processo:
            raise GptActionsError("Processo não encontrado.", 404)

        enriched = ProcessoSetupStatsService().enrich_processos([processo])[0]
        process_json = row_to_json(enriched) or {}

        instancias_all = ProcessoInstanciaRepository().list_by_processo(processo_id)
        instancias = filter_rows_for_access(
            request, instancias_all, codigo_key="codigo_filial"
        )
        instancia_ids = {str(i.get("instancia_id") or "") for i in instancias}

        selected_instance_id = (instance_id or "").strip() or None
        if selected_instance_id:
            self._raise(check_instancia_view_access(request, selected_instance_id))
            if selected_instance_id not in instancia_ids:
                # Fail closed: do not expand scope via parent process linkage alone.
                raise GptActionsError(
                    "Instância fora do escopo visível ou não pertence ao processo.",
                    403,
                )

        revisoes_all = RevisaoRepository().list_by_processo(processo_id)
        revisoes = [
            r
            for r in revisoes_all
            if not str(r.get("instancia_id") or "")
            or str(r.get("instancia_id") or "") in instancia_ids
        ]
        if selected_instance_id:
            revisoes = [
                r
                for r in revisoes
                if str(r.get("instancia_id") or "") == selected_instance_id
            ]

        selected_revision_id = (revision_id or "").strip() or None
        selected_revision = None
        if selected_revision_id:
            selected_revision = next(
                (
                    r
                    for r in revisoes
                    if str(r.get("revisao_id") or "") == selected_revision_id
                ),
                None,
            )
            if not selected_revision:
                raise GptActionsError(
                    "Revisão não encontrada no escopo do processo/melhoria.",
                    404,
                )

        baseline = self._pick_baseline(revisoes, selected_instance_id)
        scenario = self._pick_scenario(
            revisoes,
            selected_revision=selected_revision,
            selected_instance_id=selected_instance_id,
        )

        missing: list[str] = []
        warnings: list[str] = []
        ambiguities: list[str] = []

        if not instancias:
            missing.append("instances")
            warnings.append("Process has no visible operational improvements (instances).")
        if not revisoes:
            missing.append("revisions")
        if not baseline:
            missing.append("baseline_revision")
        if not scenario:
            missing.append("comparable_scenario_revision")
        if selected_instance_id is None and len(instancias) > 1:
            ambiguities.append(
                "Multiple instances visible; pass instance_id to isolate one melhoria."
            )

        diagram_row = ProcessoDiagramRepository().get(processo_id)
        decomp_row = ProcessoDecomposicaoRepository().get(processo_id)
        has_diagram = bool(diagram_row and diagram_row.get("conteudo"))
        has_decomp = bool(decomp_row and decomp_row.get("conteudo"))
        if not has_diagram:
            missing.append("process_diagram")
        if not has_decomp:
            missing.append("decomposition_tree")

        as_is = self._revision_snapshot(baseline, label="as_is")
        to_be = self._revision_snapshot(scenario, label="to_be")

        if baseline and not as_is.get("measurement"):
            missing.append("baseline_measurement")
        if scenario and not to_be.get("measurement"):
            missing.append("scenario_measurement")

        comparison = None
        try:
            comparison = ProcessRevisionCompareService().compare(processo_id)
        except Exception:
            warnings.append("process_revision_compare_unavailable")

        impact_effort = None
        matrix_target = selected_instance_id or (
            str((scenario or baseline or {}).get("instancia_id") or "") or None
        )
        if matrix_target:
            try:
                impact_effort = RevisaoImpactEffortMatrixService().build_for_instancia(
                    matrix_target
                )
            except Exception:
                warnings.append("impact_effort_unavailable")
        elif scenario:
            try:
                impact_effort = RevisaoImpactEffortMatrixService().build_for_revisao(
                    str(scenario.get("revisao_id"))
                )
            except Exception:
                warnings.append("impact_effort_unavailable")

        composed_diagram = None
        composed_decomp = None
        try:
            composed_diagram = DiagramaCompositionService().compose_for_processo(
                processo_id,
                instancia_id=selected_instance_id,
            )
        except Exception:
            warnings.append("diagram_composition_unavailable")
        try:
            composed_decomp = DecomposicaoCompositionService().compose_for_processo(
                processo_id,
                instancia_id=selected_instance_id,
            )
        except Exception:
            warnings.append("decomposition_composition_unavailable")

        graph = self._build_graph(
            process_id=processo_id,
            process=process_json,
            instances=instancias,
            revisions=revisoes,
            has_diagram=has_diagram,
            has_decomp=has_decomp,
            as_is=as_is,
            to_be=to_be,
        )

        resources = self._collect_resources(as_is, to_be)

        return {
            "context_version": CONTEXT_VERSION,
            "process": process_json,
            "process_graph": graph,
            "instances": rows_to_json(instancias),
            "revisions": rows_to_json(revisoes),
            "selection": {
                "process_id": processo_id,
                "instance_id": selected_instance_id,
                "revision_id": selected_revision_id
                or (str(scenario.get("revisao_id")) if scenario else None),
                "baseline_revisao_id": str(baseline.get("revisao_id"))
                if baseline
                else None,
                "scenario_revisao_id": str(scenario.get("revisao_id"))
                if scenario
                else None,
            },
            "baseline": as_is,
            "scenario": to_be,
            "as_is": {
                "revision": as_is.get("revision"),
                "measurement": as_is.get("measurement"),
                "investments": as_is.get("investments") or [],
                "diagram_composed_present": bool(composed_diagram),
                "decomposition_composed_present": bool(composed_decomp),
                "mermaid": (composed_diagram or {}).get("mermaid")
                if isinstance(composed_diagram, dict)
                else None,
                "epistemic_status": "OBSERVED" if baseline else "UNKNOWN",
            },
            "to_be": {
                "revision": to_be.get("revision"),
                "measurement": to_be.get("measurement"),
                "investments": to_be.get("investments") or [],
                "epistemic_status": "OBSERVED" if scenario else "UNKNOWN",
            },
            "comparison": comparison,
            "impact_effort": impact_effort,
            "resources": resources,
            "artifacts": {
                "process_diagram_present": has_diagram,
                "decomposition_tree_present": has_decomp,
                "diagram_composition": {
                    "available": composed_diagram is not None,
                    "epistemic_status": "CALCULATED"
                    if composed_diagram is not None
                    else "UNKNOWN",
                },
                "decomposition_composition": {
                    "available": composed_decomp is not None,
                    "epistemic_status": "CALCULATED"
                    if composed_decomp is not None
                    else "UNKNOWN",
                },
            },
            "data_quality": {
                "missing": missing,
                "warnings": warnings,
                "ambiguities": ambiguities,
            },
            "capabilities": {
                "quick_registration": True,
                "guided_transformation": True,
                "write_records": True,
                "write_improvement_package": True,
                "write_diagram_validated": False,
                "write_decomposition_validated": False,
                "persist_diagram_via_gpt": False,
                "conversational_draft_flows": True,
                "side_effect": False,
            },
        }

    def _raise(self, err) -> None:
        if err is not None:
            # JSONResponse from branch_access_http
            detail = getattr(err, "body", None)
            message = "Acesso negado."
            status = getattr(err, "status_code", 403) or 403
            try:
                import json

                payload = json.loads(err.body.decode() if isinstance(err.body, bytes) else err.body)
                message = payload.get("message") or message
            except Exception:
                pass
            raise GptActionsError(message, status)

    def _pick_baseline(
        self, revisoes: list[dict[str, Any]], instance_id: str | None
    ) -> dict[str, Any] | None:
        pool = revisoes
        if instance_id:
            pool = [
                r for r in revisoes if str(r.get("instancia_id") or "") == instance_id
            ]
        baselines = [
            r
            for r in pool
            if str(r.get("cenario_tipo") or "").lower() == "baseline"
        ]
        if not baselines:
            return None
        return sorted(
            baselines,
            key=lambda r: str(r.get("data_inicio_vigencia") or ""),
        )[0]

    def _pick_scenario(
        self,
        revisoes: list[dict[str, Any]],
        *,
        selected_revision: dict[str, Any] | None,
        selected_instance_id: str | None,
    ) -> dict[str, Any] | None:
        if selected_revision:
            tipo = str(selected_revision.get("cenario_tipo") or "").lower()
            if tipo != "baseline":
                return selected_revision
        pool = revisoes
        if selected_instance_id:
            pool = [
                r
                for r in revisoes
                if str(r.get("instancia_id") or "") == selected_instance_id
            ]
        comparable = [
            r
            for r in pool
            if str(r.get("cenario_tipo") or "").lower()
            in {"melhoria", "automacao", "correcao"}
        ]
        if not comparable:
            return None
        active = [r for r in comparable if r.get("revisao_ativa")]
        if active:
            return active[0]
        return sorted(
            comparable,
            key=lambda r: str(r.get("data_inicio_vigencia") or ""),
            reverse=True,
        )[0]

    def _revision_snapshot(
        self, revisao: dict[str, Any] | None, *, label: str
    ) -> dict[str, Any]:
        if not revisao:
            return {
                "revision": None,
                "measurement": None,
                "investments": [],
                "resource_links": [],
                "epistemic_status": "UNKNOWN",
                "role": label,
            }
        rid = str(revisao.get("revisao_id") or "")
        measurement = MedicaoRepository().get_by_revisao(rid) if rid else None
        investments = InvestimentoRepository().list_by_revisao(rid) if rid else []
        links = VinculoRepository().list_by_revisao(rid) if rid else []
        return {
            "revision": row_to_json(revisao),
            "measurement": row_to_json(measurement),
            "investments": rows_to_json(investments),
            "resource_links": rows_to_json(links),
            "epistemic_status": "OBSERVED",
            "role": label,
        }

    def _collect_resources(
        self, as_is: dict[str, Any], to_be: dict[str, Any]
    ) -> dict[str, Any]:
        links = list(as_is.get("resource_links") or []) + list(
            to_be.get("resource_links") or []
        )
        return {
            "links": links,
            "count": len(links),
            "epistemic_status": "OBSERVED" if links else "UNKNOWN",
        }

    def _build_graph(
        self,
        *,
        process_id: str,
        process: dict[str, Any],
        instances: list[dict[str, Any]],
        revisions: list[dict[str, Any]],
        has_diagram: bool,
        has_decomp: bool,
        as_is: dict[str, Any],
        to_be: dict[str, Any],
    ) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = [
            {
                "id": f"process:{process_id}",
                "type": "process",
                "ref_id": process_id,
                "label": process.get("nome_processo") or process_id,
            }
        ]
        edges: list[dict[str, Any]] = []

        for inst in instances:
            iid = str(inst.get("instancia_id") or "")
            if not iid:
                continue
            nodes.append(
                {
                    "id": f"instance:{iid}",
                    "type": "instance",
                    "ref_id": iid,
                    "label": inst.get("rotulo_instancia")
                    or inst.get("resumo_melhoria")
                    or iid,
                }
            )
            edges.append(
                {
                    "id": f"has_instance:{process_id}:{iid}",
                    "type": "has_instance",
                    "from": f"process:{process_id}",
                    "to": f"instance:{iid}",
                }
            )

        for rev in revisions:
            rid = str(rev.get("revisao_id") or "")
            if not rid:
                continue
            nodes.append(
                {
                    "id": f"revision:{rid}",
                    "type": "revision",
                    "ref_id": rid,
                    "label": f"{rev.get('versao_revisao') or rid} ({rev.get('cenario_tipo')})",
                    "cenario_tipo": rev.get("cenario_tipo"),
                }
            )
            iid = str(rev.get("instancia_id") or "")
            if iid:
                edges.append(
                    {
                        "id": f"has_revision:{iid}:{rid}",
                        "type": "has_revision",
                        "from": f"instance:{iid}",
                        "to": f"revision:{rid}",
                    }
                )
            else:
                edges.append(
                    {
                        "id": f"has_revision:{process_id}:{rid}",
                        "type": "has_revision",
                        "from": f"process:{process_id}",
                        "to": f"revision:{rid}",
                    }
                )
            ref = str(rev.get("revisao_referencia_id") or "").strip()
            if ref:
                edges.append(
                    {
                        "id": f"references:{rid}:{ref}",
                        "type": "references",
                        "from": f"revision:{rid}",
                        "to": f"revision:{ref}",
                    }
                )

        for snapshot, edge_type in (
            (as_is, "measured_by"),
            (to_be, "measured_by"),
        ):
            rev = snapshot.get("revision") or {}
            rid = str(rev.get("revisao_id") or "")
            med = snapshot.get("measurement") or {}
            mid = str(med.get("medicao_id") or "")
            if rid and mid:
                nodes.append(
                    {
                        "id": f"measurement:{mid}",
                        "type": "measurement",
                        "ref_id": mid,
                    }
                )
                edges.append(
                    {
                        "id": f"{edge_type}:{rid}:{mid}",
                        "type": edge_type,
                        "from": f"revision:{rid}",
                        "to": f"measurement:{mid}",
                    }
                )
            for inv in snapshot.get("investments") or []:
                iid = str(inv.get("investimento_id") or "")
                if rid and iid:
                    nodes.append(
                        {
                            "id": f"investment:{iid}",
                            "type": "investment",
                            "ref_id": iid,
                            "label": inv.get("descricao_item"),
                        }
                    )
                    edges.append(
                        {
                            "id": f"has_investment:{rid}:{iid}",
                            "type": "has_investment",
                            "from": f"revision:{rid}",
                            "to": f"investment:{iid}",
                        }
                    )
            for link in snapshot.get("resource_links") or []:
                lid = str(link.get("vinculo_id") or "")
                recurso = str(
                    link.get("recurso_compartilhado_id") or link.get("recurso_id") or ""
                )
                if rid and lid:
                    nodes.append(
                        {
                            "id": f"resource_link:{lid}",
                            "type": "resource_link",
                            "ref_id": lid,
                            "recurso_id": recurso or None,
                        }
                    )
                    edges.append(
                        {
                            "id": f"uses_resource:{rid}:{lid}",
                            "type": "uses_resource",
                            "from": f"revision:{rid}",
                            "to": f"resource_link:{lid}",
                        }
                    )

        if has_diagram:
            nodes.append(
                {
                    "id": f"diagram:{process_id}",
                    "type": "process_diagram",
                    "ref_id": process_id,
                }
            )
            edges.append(
                {
                    "id": f"modeled_by:{process_id}",
                    "type": "modeled_by",
                    "from": f"process:{process_id}",
                    "to": f"diagram:{process_id}",
                }
            )
        if has_decomp:
            nodes.append(
                {
                    "id": f"decomposition:{process_id}",
                    "type": "decomposition_tree",
                    "ref_id": process_id,
                }
            )
            edges.append(
                {
                    "id": f"decomposed_by:{process_id}",
                    "type": "decomposed_by",
                    "from": f"process:{process_id}",
                    "to": f"decomposition:{process_id}",
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "epistemic_status": "OBSERVED",
            "persistence": False,
        }
