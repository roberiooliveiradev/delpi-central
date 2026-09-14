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
_DIAGRAM_UNAVAILABLE_V1 = (
    "revision_specific_as_is_or_to_be_diagram_not_available_in_v1"
)


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

        process_json = row_to_json(processo) or {}

        instancias_all = ProcessoInstanciaRepository().list_by_processo(processo_id)
        instancias_visible = filter_rows_for_access(
            request, instancias_all, codigo_key="codigo_filial"
        )
        instancia_ids = {
            str(i.get("instancia_id") or "") for i in instancias_visible if i.get("instancia_id")
        }

        selected_instance_id = (instance_id or "").strip() or None
        selected_revision_id = (revision_id or "").strip() or None

        revisoes_all = RevisaoRepository().list_by_processo(processo_id)
        revisoes_visible = [
            r
            for r in revisoes_all
            if not str(r.get("instancia_id") or "")
            or str(r.get("instancia_id") or "") in instancia_ids
        ]

        missing: list[str] = []
        warnings: list[str] = []
        ambiguities: list[str] = []
        requires_instance_selection = False

        selected_revision = None
        if selected_revision_id:
            selected_revision = next(
                (
                    r
                    for r in revisoes_visible
                    if str(r.get("revisao_id") or "") == selected_revision_id
                ),
                None,
            )
            if not selected_revision:
                raise GptActionsError(
                    "Revisão não encontrada no escopo do processo/melhoria.",
                    404,
                )
            rev_instance_id = str(selected_revision.get("instancia_id") or "").strip() or None
            if rev_instance_id:
                if selected_instance_id and selected_instance_id != rev_instance_id:
                    raise GptActionsError(
                        "revision_id does not belong to the given instance_id.",
                        400,
                    )
                selected_instance_id = rev_instance_id

        if selected_instance_id:
            self._raise(check_instancia_view_access(request, selected_instance_id))
            if selected_instance_id not in instancia_ids:
                raise GptActionsError(
                    "Instância fora do escopo visível ou não pertence ao processo.",
                    403,
                )
        elif len(instancias_visible) > 1:
            requires_instance_selection = True
            ambiguities.append("requires_instance_selection")
        elif len(instancias_visible) == 1:
            selected_instance_id = str(instancias_visible[0].get("instancia_id") or "") or None

        if selected_instance_id:
            instancias = [
                i
                for i in instancias_visible
                if str(i.get("instancia_id") or "") == selected_instance_id
            ]
            revisoes = [
                r
                for r in revisoes_visible
                if str(r.get("instancia_id") or "") == selected_instance_id
            ]
        else:
            instancias = list(instancias_visible)
            revisoes = list(revisoes_visible)

        allowed_revision_ids = {
            str(r.get("revisao_id") or "") for r in revisoes if r.get("revisao_id")
        }

        baseline = None
        scenario = None
        if not requires_instance_selection:
            baseline = self._pick_baseline(revisoes, selected_instance_id)
            scenario = self._pick_scenario(
                revisoes,
                selected_revision=selected_revision,
                selected_instance_id=selected_instance_id,
            )
            if baseline and scenario:
                b_inst = str(baseline.get("instancia_id") or "")
                s_inst = str(scenario.get("instancia_id") or "")
                if b_inst and s_inst and b_inst != s_inst:
                    warnings.append("baseline_scenario_instance_mismatch_blocked")
                    baseline = None
                    scenario = None

        if not instancias:
            missing.append("instances")
            warnings.append("Process has no visible operational improvements (instances).")
        if not revisoes:
            missing.append("revisions")
        if requires_instance_selection:
            missing.append("instance_selection")
            missing.append("baseline_revision")
            missing.append("comparable_scenario_revision")
        else:
            if not baseline:
                missing.append("baseline_revision")
            if not scenario:
                missing.append("comparable_scenario_revision")

        diagram_row = ProcessoDiagramRepository().get(processo_id)
        decomp_row = ProcessoDecomposicaoRepository().get(processo_id)
        has_diagram = bool(diagram_row and diagram_row.get("conteudo"))
        has_decomp = bool(decomp_row and decomp_row.get("conteudo"))
        if not has_diagram:
            missing.append("process_diagram")
        if not has_decomp:
            missing.append("decomposition_tree")

        process_json["visible_scope_stats"] = self._visible_scope_stats(
            instances=instancias_visible if requires_instance_selection else instancias,
            revisions=revisoes_visible if requires_instance_selection else revisoes,
            has_diagram=has_diagram,
            has_decomp=has_decomp,
            diagram_row=diagram_row,
            decomp_row=decomp_row,
        )

        as_is = self._revision_snapshot(baseline, label="as_is")
        to_be = self._revision_snapshot(scenario, label="to_be")

        if baseline and not as_is.get("measurement"):
            missing.append("baseline_measurement")
        if scenario and not to_be.get("measurement"):
            missing.append("scenario_measurement")

        comparison = None
        try:
            raw_comparison = ProcessRevisionCompareService().compare(processo_id)
            comparison = self._filter_comparison(raw_comparison, allowed_revision_ids)
        except Exception:
            warnings.append("process_revision_compare_unavailable")

        impact_effort = None
        if selected_instance_id and not requires_instance_selection:
            try:
                impact_effort = RevisaoImpactEffortMatrixService().build_for_instancia(
                    selected_instance_id
                )
            except Exception:
                warnings.append("impact_effort_unavailable")

        composed_diagram = None
        composed_decomp = None
        # Never compose with instancia_id=None: that loads all process revisions
        # and can mix unauthorized instance overlays.
        if selected_instance_id and not requires_instance_selection:
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
        elif requires_instance_selection:
            ambiguities.append("composition_requires_instance_selection")

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

        selection_resolved = not requires_instance_selection and bool(
            selected_instance_id or selected_revision_id or baseline or scenario
        )

        return {
            "context_version": CONTEXT_VERSION,
            "process": process_json,
            "process_graph": graph,
            "instances": rows_to_json(instancias),
            "revisions": rows_to_json(revisoes),
            "selection": {
                "process_id": processo_id,
                "instance_id": selected_instance_id,
                "revision_id": selected_revision_id,
                "baseline_revisao_id": str(baseline.get("revisao_id"))
                if baseline
                else None,
                "scenario_revisao_id": str(scenario.get("revisao_id"))
                if scenario
                else None,
                "resolved": selection_resolved and not requires_instance_selection,
                "requires_instance_selection": requires_instance_selection,
            },
            "baseline": as_is,
            "scenario": to_be,
            "as_is": {
                "role": "AS_IS",
                "revision": as_is.get("revision"),
                "measurement": as_is.get("measurement"),
                "investments": as_is.get("investments") or [],
                "mermaid": None,
                "diagram": {
                    "epistemic_status": "UNKNOWN",
                    "reason": _DIAGRAM_UNAVAILABLE_V1,
                },
                "epistemic_status": "OBSERVED" if baseline else "UNKNOWN",
            },
            "to_be": {
                "role": "TO_BE",
                "revision": to_be.get("revision"),
                "measurement": to_be.get("measurement"),
                "investments": to_be.get("investments") or [],
                "mermaid": None,
                "diagram": {
                    "epistemic_status": "UNKNOWN",
                    "reason": _DIAGRAM_UNAVAILABLE_V1,
                },
                "epistemic_status": "OBSERVED" if scenario else "UNKNOWN",
            },
            "current_composed": {
                "role": "CURRENT_COMPOSED",
                "instance_id": selected_instance_id
                if selected_instance_id and not requires_instance_selection
                else None,
                "diagram_available": composed_diagram is not None,
                "decomposition_available": composed_decomp is not None,
                "mermaid": (composed_diagram or {}).get("mermaid")
                if isinstance(composed_diagram, dict)
                else None,
                "epistemic_status": "CALCULATED"
                if composed_diagram is not None
                else "UNKNOWN",
                "note": (
                    "Temporal composition of process macro + overlays for the "
                    "authorized selected instance only. Not AS-IS baseline."
                ),
            },
            "comparison": comparison,
            "impact_effort": impact_effort,
            "resources": resources,
            "artifacts": {
                "process_diagram_present": has_diagram,
                "decomposition_tree_present": has_decomp,
                "diagram_composition": {
                    "available": composed_diagram is not None,
                    "role": "CURRENT_COMPOSED",
                    "epistemic_status": "CALCULATED"
                    if composed_diagram is not None
                    else "UNKNOWN",
                },
                "decomposition_composition": {
                    "available": composed_decomp is not None,
                    "role": "CURRENT_COMPOSED",
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
            "surface_supports": {
                "quick_registration": True,
                "guided_transformation": True,
                "records_api": True,
                "improvement_package_api": True,
                "diagram_validated_write": False,
                "decomposition_validated_write": False,
                "persist_diagram_via_gpt": False,
                "conversational_draft_flows": True,
                "side_effect": False,
                "support_vs_authorization": (
                    "surface_supports describes API surface only; "
                    "write authorization is enforced by the backend at write time"
                ),
            },
        }

    def _raise(self, err) -> None:
        if err is not None:
            message = "Acesso negado."
            status = getattr(err, "status_code", 403) or 403
            try:
                import json

                payload = json.loads(
                    err.body.decode() if isinstance(err.body, bytes) else err.body
                )
                message = payload.get("message") or message
            except Exception:
                pass
            raise GptActionsError(message, status)

    def _visible_scope_stats(
        self,
        *,
        instances: list[dict[str, Any]],
        revisions: list[dict[str, Any]],
        has_diagram: bool,
        has_decomp: bool,
        diagram_row: dict[str, Any] | None,
        decomp_row: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Stats derived only from already-authorized visible records."""
        diagram_nodes = 0
        if has_diagram and isinstance((diagram_row or {}).get("conteudo"), dict):
            nodes = (diagram_row or {}).get("conteudo", {}).get("nodes") or []
            diagram_nodes = len(nodes) if isinstance(nodes, list) else 0
        decomp_nodes = 0
        if has_decomp and isinstance((decomp_row or {}).get("conteudo"), dict):
            nodes = (decomp_row or {}).get("conteudo", {}).get("nodes") or []
            decomp_nodes = len(nodes) if isinstance(nodes, list) else 0

        has_baseline = any(
            str(r.get("cenario_tipo") or "").lower() == "baseline" for r in revisions
        )
        has_melhoria = any(
            str(r.get("cenario_tipo") or "").lower()
            in {"melhoria", "automacao", "correcao"}
            for r in revisions
        )
        has_medicao = False
        for r in revisions:
            rid = str(r.get("revisao_id") or "")
            if rid and MedicaoRepository().get_by_revisao(rid):
                has_medicao = True
                break

        return {
            "instancia_count": len(instances),
            "diagram_node_count": diagram_nodes,
            "decomposition_node_count": decomp_nodes,
            "has_baseline": has_baseline,
            "has_melhoria": has_melhoria,
            "has_medicao": has_medicao,
            "scope": "visible_authorized_only",
        }

    def _filter_comparison(
        self,
        comparison: dict[str, Any] | None,
        allowed_revision_ids: set[str],
    ) -> dict[str, Any] | None:
        if not comparison:
            return comparison
        items = [
            item
            for item in (comparison.get("items") or [])
            if str(item.get("revisao_id") or "") in allowed_revision_ids
        ]
        filtered = dict(comparison)
        filtered["items"] = items
        filtered["total_revisoes"] = len(items)
        return filtered

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
