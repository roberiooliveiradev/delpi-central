from typing import Any
from urllib.parse import quote
from uuid import UUID

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


class ExecuteExternalActionUseCase:
    INTERNAL_PARAMETER_NAMES = {
        "message",
        "prompt",
        "question",
        "input",
        "text",
        "queryText",
        "query_text",
        "userMessage",
        "user_message",
        "presentationDetailFilter",
        "sessionResponseFormat",
    }

    def __init__(
        self,
        repository,
        gateway,
        policy: ExternalActionExecutionPolicy,
        audit_repository: AuditRepositoryPort,
    ):
        self.repository = repository
        self.gateway = gateway
        self.policy = policy
        self.audit_repository = audit_repository
        self.presenter = ExternalActionResultPresenter()

    def execute(
        self,
        user_id: str,
        access_token: str,
        action_id: str,
        arguments: dict,
    ) -> dict:
        action_bundle = self.repository.get_action_for_execution(action_id)

        if not action_bundle:
            raise ValueError("Action not found")

        provider = action_bundle["provider"]
        action = action_bundle["action"]
        arguments = self._normalize_arguments_for_method(action, arguments)
        pipeline_parameters = self._extract_pipeline_parameters(arguments)
        arguments = self._drop_internal_unknown_parameters(action, arguments)

        self.policy.validate(provider, action, arguments)

        gateway_parameters = self._clamp_hierarchical_query_parameters(
            action.get("path") or "",
            arguments.get("parameters") or {},
        )
        request_parameters = self._merge_pipeline_parameters(
            gateway_parameters,
            pipeline_parameters,
        )

        inferred_filter = self._infer_schedule_detail_filter(
            request_parameters,
            action_path=action.get("path") or "",
            body=arguments.get("body"),
        )

        if inferred_filter:
            request_parameters = dict(request_parameters)
            request_parameters["presentationDetailFilter"] = inferred_filter

        result = self.gateway.execute(
            provider=provider,
            action=action,
            parameters=gateway_parameters,
            body=arguments.get("body"),
            access_token=access_token,
            action_path=action.get("path") or "",
        )

        sanitized_data = self.policy.sanitize_response(result["data"])
        detail_filter = request_parameters.get("presentationDetailFilter")

        if isinstance(detail_filter, dict) and detail_filter:
            from app.domain.services.chat_presentation_detail_filter_service import (
                ChatPresentationDetailFilterService,
            )

            sanitized_data = ChatPresentationDetailFilterService.apply(
                sanitized_data,
                detail_filter,
            )

        action_path = action.get("path") or ""
        resolved_path = self._resolve_action_path(action_path, request_parameters)
        from app.domain.services.chat_sql_execution_error_interpretation_service import (
            ChatSqlExecutionErrorInterpretationService,
        )

        logical_failure = ChatSqlExecutionErrorInterpretationService.has_logical_failure(
            sanitized_data,
            path=resolved_path,
        )
        effective_ok = bool(result["ok"]) and not logical_failure

        self.audit_repository.log(
            user_id=UUID(user_id),
            action="external_action.called",
            context="external_action",
            tool_calls=[
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "provider": provider["providerKey"],
                        "actionId": action["actionId"],
                        "method": action["method"],
                        "path": resolved_path,
                        "statusCode": result["statusCode"],
                        "durationMs": result["durationMs"],
                        "sensitivity": action["sensitivity"],
                    },
                }
            ],
            metadata={
                "provider": provider["providerKey"],
                "action_id": action["actionId"],
                "method": action["method"],
                "path": resolved_path,
                "status_code": result["statusCode"],
                "duration_ms": result["durationMs"],
                "sensitivity": action["sensitivity"],
            },
        )

        presentation_metadata = self._build_presentation_metadata(
            action=action,
            sanitized_data=sanitized_data,
            resolved_path=resolved_path,
            request_parameters=request_parameters,
        )

        from app.domain.services.chat_operational_api_domain_service import (
            ChatOperationalApiDomainService,
        )

        execution_metadata = {
            "durationMs": result["durationMs"],
            "sensitivity": action["sensitivity"],
            "apiRouteDomain": ChatOperationalApiDomainService.classify_path(resolved_path),
            **presentation_metadata,
        }

        api_delpi_meta = self._extract_api_delpi_response_meta(sanitized_data)
        if api_delpi_meta:
            execution_metadata["apiDelpiResponseMeta"] = api_delpi_meta

        if not effective_ok:
            api_error = self._extract_api_error_message(sanitized_data)

            if api_error:
                execution_metadata["error"] = api_error

        return {
            "provider": provider["providerKey"],
            "actionId": action["actionId"],
            "method": action["method"],
            "path": resolved_path,
            "statusCode": result["statusCode"],
            "ok": effective_ok,
            "data": sanitized_data,
            "metadata": execution_metadata,
        }

    @staticmethod
    def _extract_api_error_message(data) -> str | None:
        from app.domain.services.chat_sql_execution_error_interpretation_service import (
            ChatSqlExecutionErrorInterpretationService,
        )

        text = ChatSqlExecutionErrorInterpretationService.extract_error_text(data)

        return text or None

    @staticmethod
    def _extract_api_delpi_response_meta(data) -> dict | None:
        if not isinstance(data, dict):
            return None
        if "meta" not in data:
            return None
        if "success" not in data and "data" not in data:
            return None
        meta = data.get("meta")
        return meta if isinstance(meta, dict) else None

    def build_metadata_for_data(
        self,
        *,
        action_id: str,
        data,
        parameters: dict | None = None,
    ) -> dict:
        action_bundle = self.repository.get_action_for_execution(action_id)

        if not action_bundle:
            raise ValueError("Action not found")

        action = action_bundle["action"]
        sanitized_data = self.policy.sanitize_response(data)
        action_path = action.get("path") or ""
        request_parameters = dict(parameters or {})
        resolved_path = self._resolve_action_path(action_path, request_parameters)

        return self._build_presentation_metadata(
            action=action,
            sanitized_data=sanitized_data,
            resolved_path=resolved_path,
            request_parameters=request_parameters,
        )

    def _build_presentation_metadata(
        self,
        *,
        action: dict,
        sanitized_data,
        resolved_path: str,
        request_parameters: dict,
    ) -> dict:
        from app.application.services.chat_presentation_metadata_pipeline_service import (
            ChatPresentationMetadataPipelineService,
        )

        return ChatPresentationMetadataPipelineService.build(
            action=action,
            sanitized_data=sanitized_data,
            resolved_path=resolved_path,
            request_parameters=request_parameters,
            presenter=self.presenter,
            extract_response_meta=self._extract_api_delpi_response_meta,
        )

    @staticmethod
    def _resolve_action_path(path: str, parameters: dict) -> str:
        resolved = str(path or "")

        for key, value in (parameters or {}).items():
            if value in (None, ""):
                continue

            token = "{" + str(key) + "}"

            if token in resolved:
                resolved = resolved.replace(
                    token,
                    quote(str(value), safe=""),
                )

        return resolved

    @staticmethod
    def _clamp_hierarchical_query_parameters(path: str, parameters: dict) -> dict:
        lowered = str(path or "").lower()

        if "/structure" not in lowered and "/parents" not in lowered:
            return dict(parameters or {})

        clamped = dict(parameters or {})
        depth_keys = {"max_depth", "maxdepth", "depth", "nivel", "levels"}

        for key, value in list(clamped.items()):
            if str(key).lower() not in depth_keys:
                continue

            try:
                depth = int(value)
            except (TypeError, ValueError):
                continue

            clamped[key] = min(max(depth, 1), 15)

        return clamped

    def _drop_internal_unknown_parameters(self, action: dict, arguments: dict) -> dict:
        normalized = dict(arguments or {})
        parameters = dict(normalized.get("parameters") or {})

        if not parameters:
            normalized["parameters"] = parameters
            return normalized

        allowed_parameter_names = {
            parameter.get("name")
            for parameter in action.get("parametersSchema") or []
            if parameter.get("name")
        }

        cleaned_parameters = {}

        for key, value in parameters.items():
            if key in allowed_parameter_names:
                cleaned_parameters[key] = value
                continue

            if key in self.INTERNAL_PARAMETER_NAMES:
                continue

            cleaned_parameters[key] = value

        normalized["parameters"] = cleaned_parameters
        return normalized

    @classmethod
    def _extract_pipeline_parameters(cls, arguments: dict) -> dict[str, Any]:
        parameters = dict((arguments or {}).get("parameters") or {})
        pipeline: dict[str, Any] = {}

        for key in cls.INTERNAL_PARAMETER_NAMES:
            value = parameters.get(key)

            if value in (None, "", {}, []):
                continue

            pipeline[key] = value

        return pipeline

    @staticmethod
    def _merge_pipeline_parameters(
        gateway_parameters: dict,
        pipeline_parameters: dict,
    ) -> dict:
        merged = dict(gateway_parameters or {})

        for key, value in (pipeline_parameters or {}).items():
            if value in (None, "", {}, []):
                continue

            merged[key] = value

        return merged

    def _normalize_arguments_for_method(self, action: dict, arguments: dict) -> dict:
        normalized = dict(arguments or {})
        method = str(action.get("method") or "").upper()

        parameters = dict(normalized.get("parameters") or {})
        body = normalized.get("body")

        if method not in {"GET", "HEAD", "DELETE"}:
            normalized["parameters"] = parameters
            return normalized

        if body in (None, "", {}, []):
            normalized["parameters"] = parameters
            normalized["body"] = None
            return normalized

        if isinstance(body, dict):
            for key, value in body.items():
                if value in (None, ""):
                    continue

                parameters.setdefault(key, value)

        normalized["parameters"] = parameters
        normalized["body"] = None

        return normalized

    @staticmethod
    def _infer_schedule_detail_filter(
        parameters: dict,
        *,
        action_path: str,
        body,
    ) -> dict[str, str] | None:
        existing = (parameters or {}).get("presentationDetailFilter")

        if isinstance(existing, dict) and str(existing.get("product_code_prefix") or "").strip():
            return None

        user_message = str((parameters or {}).get("userMessage") or "").strip()

        if not user_message and isinstance(body, dict):
            user_message = str(
                body.get("message") or body.get("query") or body.get("question") or ""
            ).strip()

        if not user_message:
            return None

        from app.domain.services.chat_production_schedule_membership_presentation_service import (
            ChatProductionScheduleMembershipPresentationService,
        )

        return ChatProductionScheduleMembershipPresentationService.resolve_detail_filter(
            user_message,
            path=action_path,
        )
