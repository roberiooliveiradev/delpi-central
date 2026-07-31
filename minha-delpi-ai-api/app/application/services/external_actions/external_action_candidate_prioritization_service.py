"""Priorização declarativa de candidatos OpenAPI — vocabulário em actionSelection JSON."""

from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionCandidatePrioritizationService:
    """Reordena/filtra candidatos por domínio KPI antes da escolha final."""

    @classmethod
    def apply(
        cls,
        message: str,
        candidates: list[dict],
        *,
        supplies_otd: bool = False,
    ) -> list[dict]:
        ordered = list(candidates)

        if supplies_otd:
            ordered = cls._prioritize_supplies_otd(message, ordered)

        ordered = cls._prioritize_production_pcp_orders(message, ordered)
        ordered = cls._prioritize_production_otd_detail(message, ordered)
        ordered = cls._prioritize_production_oee_appointment(message, ordered)
        ordered = cls._prioritize_quality_kaizen_detail(message, ordered)
        ordered = cls._prioritize_production_eficiencia_fabril(message, ordered)
        return cls._prioritize_production_oee_detail(message, ordered)

    @classmethod
    def _prioritize_production_pcp_orders(
        cls,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        trigger_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionPcpOrdersTriggerTerms",
        )
        if not any(term in normalized for term in trigger_terms):
            return candidates

        path_markers = [
            str(item).lower()
            for item in ExternalActionResponseContentService.list(
                "actionSelection",
                "productionPcpOrdersPathMarkers",
            )
            if str(item).strip()
        ]
        preferred_list = [
            str(item).lower()
            for item in ExternalActionResponseContentService.list(
                "actionSelection",
                "productionPcpOrdersPreferredOperationIds",
            )
            if str(item).strip()
        ]
        preferred_ids = set(preferred_list)
        preferred_order = {op_id: index for index, op_id in enumerate(preferred_list)}

        def _is_pcp(action: dict) -> bool:
            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()
            if operation_id in preferred_ids:
                return True
            return any(marker in path or marker in operation_id for marker in path_markers)

        pcp_actions = [action for action in candidates if _is_pcp(action)]
        if not pcp_actions:
            return candidates

        def _sort_key(action: dict) -> tuple:
            operation_id = str(action.get("operationId") or "").lower()
            return (
                preferred_order.get(operation_id, 99),
                str(action.get("path") or ""),
            )

        return sorted(pcp_actions, key=_sort_key)

    @classmethod
    def _prioritize_supplies_otd(cls, message: str, candidates: list[dict]) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        supplies_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "suppliesOtdSuppliesDomainTerms",
        )
        supplies_prefix = ExternalActionResponseContentService.get(
            "actionSelection",
            "suppliesOtdPathPrefix",
            default="/supplies/",
        ).lower()

        if any(term in normalized for term in supplies_terms):
            supplies = [
                action
                for action in candidates
                if supplies_prefix in str(action.get("path") or "").lower()
            ]

            if supplies:
                return supplies

        production_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "candidatePathPrioritization",
            "productionTerms",
        )
        commercial_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "candidatePathPrioritization",
            "commercialTerms",
        )

        if any(term in normalized for term in production_terms):
            production = [
                action
                for action in candidates
                if "/production/" in str(action.get("path") or "").lower()
            ]

            if production:
                return production

        if any(term in normalized for term in commercial_terms):
            commercial = [
                action
                for action in candidates
                if "/commercial/" in str(action.get("path") or "").lower()
            ]

            if commercial:
                return commercial

        return candidates

    @classmethod
    def _prioritize_production_otd_detail(
        cls,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        detail_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOtdDetailTerms",
        )
        production_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOtdDetailProductionContextTerms",
        )

        if not any(term in normalized for term in detail_terms):
            return candidates
        if not any(term in normalized for term in production_terms):
            return candidates

        detail_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOtdDetailPath",
            default="/production/otd",
        ).lower()
        detail_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOtdDetailOperationId",
            default="get_production_otd",
        ).lower()

        detail_actions = [
            action
            for action in candidates
            if (
                str(action.get("path") or "").lower().rstrip("/") == detail_path.rstrip("/")
                or detail_operation in str(action.get("operationId") or "").lower()
            )
        ]

        return detail_actions or candidates

    @classmethod
    def _prioritize_production_oee_appointment(
        cls,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        appointment_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOeeAppointmentTerms",
        )
        oee_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOeeContextTerms",
        )
        appointment_context_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOeeAppointmentShortcutTerms",
        )

        if not any(term in normalized for term in appointment_terms):
            return candidates
        if not any(term in normalized for term in oee_terms):
            if not any(term in normalized for term in appointment_context_terms):
                return candidates

        appointment_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOeeAppointmentPath",
            default="/production/oee/appointments/",
        ).lower()
        appointment_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOeeAppointmentOperationId",
            default="get_production_oee_appointment_by_id",
        ).lower()

        appointment_actions = [
            action
            for action in candidates
            if (
                appointment_path.rstrip("/")
                in str(action.get("path") or "").lower().rstrip("/")
                or appointment_operation
                in str(action.get("operationId") or "").lower()
            )
        ]

        return appointment_actions or candidates

    @classmethod
    def _prioritize_quality_kaizen_detail(
        cls,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        detail_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "qualityKaizenDetailTerms",
        )
        kaizen_context_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "qualityKaizenContextTerms",
        )

        if not any(term in normalized for term in detail_terms):
            return candidates
        if not any(term in normalized for term in kaizen_context_terms):
            return candidates

        detail_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "qualityKaizenDetailPath",
            default="/quality/kaizens/",
        ).lower()
        detail_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "qualityKaizenDetailOperationId",
            default="get_kaizen_by_id",
        ).lower()

        detail_actions = [
            action
            for action in candidates
            if (
                detail_path.rstrip("/")
                in str(action.get("path") or "").lower().rstrip("/")
                or detail_operation in str(action.get("operationId") or "").lower()
            )
        ]

        return detail_actions or candidates

    @classmethod
    def _prioritize_production_eficiencia_fabril(
        cls,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        fabril_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionEficienciaFabrilTerms",
        )
        if not any(term in normalized for term in fabril_terms):
            appointments_terms = ExternalActionResponseContentService.list(
                "actionSelection",
                "productionEficienciaFabrilAppointmentsTerms",
            )
            if not any(term in normalized for term in appointments_terms):
                return candidates

        appointments_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionEficienciaFabrilAppointmentsPath",
            default="/production/eficiencia-fabril/appointments",
        ).lower()
        appointments_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionEficienciaFabrilAppointmentsOperationId",
            default="list_eficiencia_fabril_appointments",
        ).lower()

        if any(
            term in normalized
            for term in ExternalActionResponseContentService.list(
                "actionSelection",
                "productionEficienciaFabrilAppointmentsTerms",
            )
        ):
            appointment_actions = [
                action
                for action in candidates
                if (
                    str(action.get("path") or "").lower().rstrip("/")
                    == appointments_path.rstrip("/")
                    or appointments_operation
                    in str(action.get("operationId") or "").lower()
                )
            ]
            if appointment_actions:
                return appointment_actions

        dashboard_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionEficienciaFabrilDashboardPath",
            default="/production/eficiencia-fabril/dashboard",
        ).lower()
        dashboard_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionEficienciaFabrilDashboardOperationId",
            default="get_eficiencia_fabril_dashboard",
        ).lower()

        dashboard_actions = [
            action
            for action in candidates
            if (
                str(action.get("path") or "").lower().rstrip("/") == dashboard_path.rstrip("/")
                or dashboard_operation in str(action.get("operationId") or "").lower()
            )
        ]

        return dashboard_actions or candidates

    @classmethod
    def _prioritize_production_oee_detail(
        cls,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        detail_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOeeDetailTerms",
        )
        oee_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOeeContextTerms",
        )
        fabril_block_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOeeFabrilBlockTerms",
        )

        if any(term in normalized for term in fabril_block_terms):
            return candidates

        if not any(term in normalized for term in detail_terms):
            return candidates
        if not any(term in normalized for term in oee_terms):
            return candidates

        detail_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOeeDetailPath",
            default="/production/oee",
        ).lower()
        detail_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOeeDetailOperationId",
            default="get_production_oee",
        ).lower()

        detail_actions = [
            action
            for action in candidates
            if (
                str(action.get("path") or "").lower().rstrip("/") == detail_path.rstrip("/")
                or detail_operation in str(action.get("operationId") or "").lower()
            )
        ]

        return detail_actions or candidates
