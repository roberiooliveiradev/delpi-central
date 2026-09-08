"""Planner estruturado: top-K → ActionPlan (OpenAPI schema, sem free-pick)."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from app.domain.models.action_descriptor import ActionCandidate
from app.domain.models.action_plan import ActionPlan, ActionPlanStep
from app.domain.services.chat_agentic_action_schema_service import (
    ChatAgenticActionSchemaService,
)
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)

_IDENTIFIER_RE = re.compile(r"\b(\d{4,})\b")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{3,}")


class PlanExternalActionsService:
    def __init__(
        self,
        *,
        llm_planner: Callable[[str, list[dict[str, Any]]], dict[str, Any] | None] | None = None,
    ) -> None:
        self.llm_planner = llm_planner

    def plan(
        self,
        message: str,
        candidates: list[ActionCandidate],
        *,
        previous_messages: list | None = None,
        execution_context: dict[str, Any] | None = None,
        max_steps: int | None = None,
    ) -> ActionPlan:
        if not candidates:
            return ActionPlan(selection_mode="openapi_first")

        top_k_ids = {item.action_id for item in candidates if item.action_id}
        slim_catalog = [
            ChatAgenticActionSchemaService.build_slim_action(
                item.raw_action,
                prefer_openapi_examples=True,
            )
            for item in candidates
        ]
        slim_catalog = [entry for entry in slim_catalog if entry]

        limit = max_steps or OpenApiToolRoutingContentService.int_setting(
            "planner",
            "maxSteps",
            default=3,
        )

        llm_payload: dict[str, Any] | None = None
        if self.llm_planner is not None:
            try:
                llm_payload = self.llm_planner(message, slim_catalog)
            except Exception:
                llm_payload = None

        if isinstance(llm_payload, dict):
            plan = self._plan_from_payload(llm_payload, top_k_ids=top_k_ids, limit=limit)
            if plan.clarify and plan.is_empty:
                return plan
            if not plan.is_empty:
                enriched = self._enrich_plan_with_bound_arguments(
                    message,
                    plan,
                    candidates,
                    previous_messages=previous_messages,
                    execution_context=execution_context,
                )
                # If the LLM chose an action but binding cannot satisfy required
                # args, prefer the deterministic ranker for this subtask.
                if not (enriched.clarify and enriched.is_empty):
                    return enriched

        return self._deterministic_plan(
            message,
            candidates,
            previous_messages=previous_messages,
            execution_context=execution_context,
            limit=limit,
        )

    def _enrich_plan_with_bound_arguments(
        self,
        message: str,
        plan: ActionPlan,
        candidates: list[ActionCandidate],
        *,
        previous_messages: list | None,
        execution_context: dict[str, Any] | None,
    ) -> ActionPlan:
        """Merge canonical `_bind_arguments` into LLM steps (fill missing required only)."""
        by_id = {item.action_id: item for item in candidates if item.action_id}
        ctx_params: dict[str, Any] = {}
        if isinstance(execution_context, dict):
            raw_params = execution_context.get("parameters")
            if isinstance(raw_params, dict):
                ctx_params = dict(raw_params)

        enriched: list[ActionPlanStep] = []
        for step in plan.steps:
            candidate = by_id.get(step.action_id)
            if candidate is None:
                enriched.append(step)
                continue

            existing_args = dict(step.arguments or {})
            existing_params = existing_args.get("parameters")
            if not isinstance(existing_params, dict):
                existing_params = {}
            existing_body = (
                existing_args.get("body")
                if isinstance(existing_args.get("body"), dict)
                else None
            )
            merged_context = {**ctx_params, **existing_params}

            parameters, body, missing = self._bind_arguments(
                message,
                candidate.raw_action,
                context_parameters=merged_context,
                previous_messages=previous_messages,
                context_body=existing_body,
            )
            if missing:
                clarify = OpenApiToolRoutingContentService.get(
                    "selectionReasons",
                    "openapiFirstClarify",
                )
                from app.domain.services.external_actions.external_action_response_content_service import (
                    ExternalActionResponseContentService,
                )

                clarify = ExternalActionResponseContentService.format(
                    "selectionReasons",
                    "missingRequiredParameter",
                    default=clarify,
                    parameter=", ".join(missing),
                )
                return ActionPlan(
                    clarify=clarify,
                    selection_mode=plan.selection_mode or "openapi_first",
                    metadata={
                        **dict(plan.metadata or {}),
                        "missingParameters": missing,
                        "actionId": step.action_id,
                    },
                )

            arguments: dict[str, Any] = {
                **existing_args,
                "actionId": step.action_id,
                "parameters": parameters,
            }
            if body is not None:
                arguments["body"] = body
            elif "body" in existing_args:
                arguments["body"] = existing_args["body"]

            enriched.append(
                ActionPlanStep(
                    action_id=step.action_id,
                    arguments=arguments,
                    reason=step.reason,
                    confidence=step.confidence,
                )
            )

        return ActionPlan(
            steps=tuple(enriched),
            clarify=plan.clarify,
            selection_mode=plan.selection_mode or "openapi_first",
            metadata=dict(plan.metadata or {}),
        )

    def _plan_from_payload(
        self,
        payload: dict[str, Any],
        *,
        top_k_ids: set[str],
        limit: int,
    ) -> ActionPlan:
        plan = ActionPlan.from_dict(payload)
        accepted: list[ActionPlanStep] = []
        for step in plan.steps:
            if step.action_id not in top_k_ids:
                continue
            accepted.append(step)
            if len(accepted) >= limit:
                break

        rejected = [
            step.action_id
            for step in plan.steps
            if step.action_id and step.action_id not in top_k_ids
        ]
        metadata = dict(plan.metadata or {})
        if rejected:
            metadata["rejectedOutsideTopK"] = rejected

        return ActionPlan(
            steps=tuple(accepted),
            clarify=plan.clarify,
            selection_mode="openapi_first",
            metadata=metadata,
        )

    def _deterministic_plan(
        self,
        message: str,
        candidates: list[ActionCandidate],
        *,
        previous_messages: list | None,
        execution_context: dict[str, Any] | None,
        limit: int,
    ) -> ActionPlan:
        normalized = (message or "").lower()
        if not normalized.strip():
            return ActionPlan(selection_mode="openapi_first")

        # Small-talk / no operational signal → empty
        if self._looks_like_small_talk(normalized) and not _IDENTIFIER_RE.search(message or ""):
            return ActionPlan(selection_mode="openapi_first")

        selected: list[ActionPlanStep] = []
        ctx_params = {}
        preferred_action_id = ""
        if isinstance(execution_context, dict):
            raw_params = execution_context.get("parameters")
            if isinstance(raw_params, dict):
                ctx_params = dict(raw_params)
            preferred_action_id = str(execution_context.get("actionId") or "").strip()

        ranked = sorted(
            candidates,
            key=lambda item: (
                -self._specificity_score(
                    normalized,
                    item,
                    preferred_action_id=preferred_action_id,
                ),
                0 if item.descriptor.method == "GET" else 1,
                len(item.descriptor.path),
            ),
        )

        for candidate in ranked:
            if len(selected) >= limit:
                break
            action = candidate.raw_action
            if not self._message_matches_action(normalized, action):
                if not (
                    candidate.score > 0.2
                    and not selected
                    and candidate is ranked[0]
                ):
                    continue

            parameters, body, missing = self._bind_arguments(
                message,
                action,
                context_parameters=ctx_params,
                previous_messages=previous_messages,
            )
            if missing:
                # Do not abort an already-valid multi-step selection because a
                # lower-ranked sibling lacks required args.
                if selected:
                    continue
                clarify = OpenApiToolRoutingContentService.get(
                    "selectionReasons",
                    "openapiFirstClarify",
                )
                from app.domain.services.external_actions.external_action_response_content_service import (
                    ExternalActionResponseContentService,
                )

                clarify = ExternalActionResponseContentService.format(
                    "selectionReasons",
                    "missingRequiredParameter",
                    default=clarify,
                    parameter=", ".join(missing),
                )
                return ActionPlan(
                    clarify=clarify,
                    selection_mode="openapi_first",
                    metadata={"missingParameters": missing, "actionId": candidate.action_id},
                )

            reason = OpenApiToolRoutingContentService.get(
                "selectionReasons",
                "openapiFirstPlan",
            )
            arguments: dict[str, Any] = {
                "actionId": candidate.action_id,
                "parameters": parameters,
            }
            if body is not None:
                arguments["body"] = body
            confidence = self._specificity_score(
                normalized,
                candidate,
                preferred_action_id=preferred_action_id,
            )
            selected.append(
                ActionPlanStep(
                    action_id=candidate.action_id,
                    arguments=arguments,
                    reason=reason,
                    confidence=round(confidence, 4),
                )
            )

            # Prefer single best match unless message clearly asks for multiple domains.
            if not self._wants_multi_action(normalized):
                break

        return ActionPlan(steps=tuple(selected), selection_mode="openapi_first")

    @classmethod
    def _looks_like_small_talk(cls, normalized: str) -> bool:
        markers = ("oi", "ola", "obrigado", "bom dia", "boa tarde", "tudo bem", "quem e voce")
        tokens = set(normalized.split())
        return any(marker in normalized for marker in markers) and len(tokens) <= 6

    @classmethod
    def _wants_multi_action(cls, normalized: str) -> bool:
        from app.application.services.decompose_external_action_requests_service import (
            DecomposeExternalActionRequestsService,
        )

        return DecomposeExternalActionRequestsService.wants_multi_action(normalized)

    @classmethod
    def _message_matches_action(cls, normalized: str, action: dict[str, Any]) -> bool:
        haystack = cls._action_haystack(action)
        if not haystack:
            return False
        tokens = [token for token in _TOKEN_RE.findall(normalized) if len(token) >= 4]
        if not tokens:
            return bool(_IDENTIFIER_RE.search(normalized))
        return any(token in haystack for token in tokens)

    @classmethod
    def _specificity_score(
        cls,
        normalized: str,
        candidate: ActionCandidate,
        *,
        preferred_action_id: str = "",
    ) -> float:
        """Score genérico: retrieve score + overlap lexical + segmentos de path/operationId.

        Sem keywords de domínio DELPI — diferencia operations próximas pelo contrato.
        """
        action = candidate.raw_action
        haystack = cls._action_haystack(action)
        tokens = [token for token in _TOKEN_RE.findall(normalized) if len(token) >= 3]
        hits = 0.0
        for token in tokens:
            if token in haystack:
                hits += 1.0 + min(len(token), 12) * 0.04

        path = str(action.get("path") or "").lower()
        operation_id = str(action.get("operationId") or action.get("operation_id") or "").lower()
        path_segments = [
            segment
            for segment in path.replace("{", " ").replace("}", " ").replace("-", " ").replace("_", " ").split()
            if len(segment) >= 3
        ]
        op_segments = [
            segment
            for segment in operation_id.replace("-", " ").replace("_", " ").split()
            if len(segment) >= 3
        ]
        segment_hits = sum(1 for segment in path_segments + op_segments if segment in normalized)

        # Prefer more specific operations when the user mentions distinctive segments
        # (excel/history/export/…) that appear in path/operationId but not in siblings.
        specificity = segment_hits * 0.85 + len(path_segments) * 0.02
        continuity = 1.25 if preferred_action_id and candidate.action_id == preferred_action_id else 0.0
        return float(candidate.score or 0.0) + hits * 0.35 + specificity + continuity

    @classmethod
    def _action_haystack(cls, action: dict[str, Any]) -> str:
        return " ".join(
            str(action.get(key) or "")
            for key in (
                "path",
                "operationId",
                "summary",
                "description",
                "actionId",
                "tags",
                "whenToUse",
            )
        ).lower()

    @classmethod
    def _bind_arguments(
        cls,
        message: str,
        action: dict[str, Any],
        *,
        context_parameters: dict[str, Any],
        previous_messages: list | None = None,
        context_body: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], Any, list[str]]:
        parameters: dict[str, Any] = {}
        for key, value in (context_parameters or {}).items():
            if value is not None and str(value).strip():
                parameters[str(key)] = value

        schema_params = action.get("parametersSchema") or action.get("parameters_schema") or []
        schema_names = {
            str(parameter.get("name") or "").strip()
            for parameter in schema_params
            if isinstance(parameter, dict) and parameter.get("name")
        }
        identifiers = _IDENTIFIER_RE.findall(message or "")
        examples = ChatAgenticActionSchemaService.collect_openapi_examples(action)

        # Product code via canônico (mensagem/contexto) — só se o schema tiver o param.
        product_param_names = {"code", "productCode", "product_code"} & schema_names
        if product_param_names and not any(name in parameters for name in product_param_names):
            from app.domain.services.chat_product_query_intent_service import (
                ChatProductQueryIntentService,
            )

            product_code = ChatProductQueryIntentService.resolve_product_code(
                message,
                previous_messages=previous_messages,
            ) or ChatProductQueryIntentService.extract_product_code(message or "")
            if not product_code:
                # OpenAPI-first: qualquer identificador alfanumérico plausível no path.
                for token in _TOKEN_RE.findall(message or ""):
                    if any(ch.isdigit() for ch in token) and len(token) >= 3:
                        product_code = token
                        break
            if product_code:
                for name in product_param_names:
                    parameters[name] = product_code

        # Date/branch via builder canônico — só aplica chaves presentes no schema OpenAPI.
        # Include granularity so required series params are filled even when dates already exist.
        date_branch_names = {
            "branch",
            "start_date",
            "end_date",
            "date_start",
            "date_end",
            "startDate",
            "endDate",
            "granularity",
        } & schema_names
        if date_branch_names and not date_branch_names.issubset(parameters.keys()):
            from app.domain.services.operational_api_parameter_builder_service import (
                OperationalApiParameterBuilderService,
            )

            built = OperationalApiParameterBuilderService().build_date_branch(
                action,
                message,
                previous_messages=previous_messages,
                base_params=parameters,
            )
            if isinstance(built, dict):
                for key, value in built.items():
                    if key in schema_names and key not in parameters and value is not None:
                        parameters[key] = value

        for parameter in schema_params:
            if not isinstance(parameter, dict):
                continue
            name = str(parameter.get("name") or "").strip()
            if not name:
                continue
            if name in parameters:
                continue
            example = examples.get(name)
            if example is not None and str(example) in (message or ""):
                parameters[name] = example
                continue
            # Path/required id-like params: bind first unused identifier.
            is_path = str(parameter.get("in") or "") == "path"
            required = bool(parameter.get("required")) or is_path
            if required and identifiers and name not in product_param_names:
                parameters[name] = identifiers[0]
                identifiers = identifiers[1:]

        body = None
        body_schema = action.get("requestBodySchema") or action.get("request_body_schema")
        missing: list[str] = []

        for parameter in schema_params:
            if not isinstance(parameter, dict):
                continue
            name = str(parameter.get("name") or "").strip()
            required = bool(parameter.get("required")) or str(parameter.get("in") or "") == "path"
            if required and name and name not in parameters:
                missing.append(name)

        if isinstance(body_schema, dict):
            required_body = cls._required_body_properties(body_schema)
            body = dict(context_body) if isinstance(context_body, dict) else {}
            for prop in required_body:
                if prop in body and body.get(prop) is not None and str(body.get(prop)).strip():
                    continue
                example = examples.get(prop)
                if example is not None and str(example).lower() in (message or "").lower():
                    body[prop] = example
                elif prop in context_parameters:
                    body[prop] = context_parameters[prop]
                else:
                    missing.append(prop)
            if not body and not required_body:
                body = None

        return parameters, body, missing

    @classmethod
    def _required_body_properties(cls, body_schema: dict[str, Any]) -> list[str]:
        content = body_schema.get("content")
        schema = None
        if isinstance(content, dict):
            for media in content.values():
                if isinstance(media, dict) and isinstance(media.get("schema"), dict):
                    schema = media["schema"]
                    break
        if schema is None and isinstance(body_schema.get("schema"), dict):
            schema = body_schema["schema"]
        if not isinstance(schema, dict):
            return []
        required = schema.get("required") or []
        return [str(item) for item in required if str(item).strip()]

    @classmethod
    def planner_json_schema(cls) -> dict[str, Any]:
        node = OpenApiToolRoutingContentService.get_node("planner", "schema")
        if isinstance(node, dict):
            return dict(node)
        return {"type": "object", "required": ["steps"]}

    @classmethod
    def dumps_schema(cls) -> str:
        return json.dumps(cls.planner_json_schema(), ensure_ascii=False)
