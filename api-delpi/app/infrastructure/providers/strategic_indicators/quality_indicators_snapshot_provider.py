from __future__ import annotations

from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.use_cases.audit_5s.get_audit_5s_summary_use_case import (
    GetAudit5SSummaryUseCase,
)
from app.application.use_cases.kaizen.get_kaizen_summary_use_case import (
    GetKaizenSummaryUseCase,
)
from app.application.use_cases.ppm.get_ppm_summary_use_case import (
    GetPpmSummaryUseCase,
)
from app.domain.ports.strategic_indicators.quality_indicators_snapshot_port import (
    StrategicIndicatorsQualityIndicatorsSnapshotPort,
)


class QualityIndicatorsSnapshotProvider(
    StrategicIndicatorsQualityIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        internal_ppm_use_case: GetPpmSummaryUseCase,
        external_ppm_use_case: GetPpmSummaryUseCase,
        kaizen_summary_use_case: GetKaizenSummaryUseCase,
        audit_5s_summary_use_case: GetAudit5SSummaryUseCase,
    ) -> None:
        self._internal_ppm_use_case = internal_ppm_use_case
        self._external_ppm_use_case = external_ppm_use_case
        self._kaizen_summary_use_case = kaizen_summary_use_case
        self._audit_5s_summary_use_case = audit_5s_summary_use_case

    def get_quality_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        self._collect_indicator(
            builder=lambda: self._build_internal_ppm_measurement(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            ),
            department_id="quality",
            source="quality_ppm_internal",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_external_ppm_measurement(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            ),
            department_id="quality",
            source="quality_ppm_external",
            items=items,
            errors=errors,
        )

        kaizen_payload = None
        try:
            kaizen_payload = self._load_kaizen_payload(
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            errors.append(
                {
                    "department_id": "quality",
                    "source": "quality_kaizen",
                    "message": str(exc),
                }
            )

        if kaizen_payload is not None:
            items.append(
                self._build_kaizen_ideas_measurement_from_payload(
                    payload=kaizen_payload,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
            items.append(
                self._build_kaizen_financial_gain_measurement_from_payload(
                    payload=kaizen_payload,
                )
            )

        self._collect_indicator(
            builder=lambda: self._build_audit_5s_measurement(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="quality",
            source="quality_audit_5s",
            items=items,
            errors=errors,
        )

        return {
            "items": items,
            "errors": errors,
        }

    def _load_kaizen_payload(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = KaizenSummaryRequest(
            title=None,
            status=None,
            date_start=start_date,
            date_end=end_date,
        )

        result = self._kaizen_summary_use_case.execute(request)
        return result.to_dict() if hasattr(result, "to_dict") else result

    def _collect_indicator(
        self,
        *,
        builder,
        department_id: str,
        source: str,
        items: list[dict],
        errors: list[dict],
    ) -> None:
        try:
            items.append(builder())
        except Exception as exc:
            errors.append(
                {
                    "department_id": department_id,
                    "source": source,
                    "message": str(exc),
                }
            )

    def _build_internal_ppm_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict:
        request = PpmSummaryRequest(
            type="internal",
            branch=branch,
            date_start=start_date,
            date_end=end_date,
        )

        result = self._internal_ppm_use_case.execute(request)
        payload = result.to_dict() if hasattr(result, "to_dict") else result

        value = self._extract_first_number(
            payload,
            ["ppm", "ppm_value", "ppm_internal", "internal_ppm", "total_ppm", "ppm_summary"],
        ) or 0.0

        unit_key = branch or "consolidated"

        return {
            "department_id": "quality",
            "indicator_id": "quality-ppm-internal",
            "value": value,
            "source": "quality_ppm_internal",
            "unit_values": {unit_key: value},
        }

    def _build_external_ppm_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict:
        request = PpmSummaryRequest(
            type="external",
            branch=branch,
            date_start=start_date,
            date_end=end_date,
        )

        result = self._external_ppm_use_case.execute(request)
        payload = result.to_dict() if hasattr(result, "to_dict") else result

        value = self._extract_first_number(
            payload,
            ["ppm", "ppm_value", "ppm_external", "external_ppm", "total_ppm", "ppm_summary"],
        ) or 0.0

        unit_key = branch or "consolidated"

        return {
            "department_id": "quality",
            "indicator_id": "quality-ppm-external",
            "value": value,
            "source": "quality_ppm_external",
            "unit_values": {unit_key: value},
        }

    def _build_kaizen_ideas_measurement_from_payload(
        self,
        *,
        payload: dict,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        total_ideas = self._extract_first_number(
            payload,
            [
                "approved_ideas_count",
                "approved_count",
                "total_approved",
                "count",
                "total_count",
                "ideas_count",
            ],
        )

        qtd_months = self._resolve_month_count(start_date=start_date, end_date=end_date)
        value = (
            round(total_ideas / qtd_months, 2)
            if total_ideas is not None and qtd_months > 0
            else (total_ideas or 0.0)
        )

        return {
            "department_id": "quality",
            "indicator_id": "quality-kaizen-ideas",
            "value": value,
            "source": "quality_kaizen_ideas",
            "unit_values": {"consolidated": value},
        }

    def _build_kaizen_financial_gain_measurement_from_payload(
        self,
        *,
        payload: dict,
    ) -> dict:
        value = self._extract_first_number(
            payload,
            [
                "financial_gain",
                "financial_gains",
                "total_financial_gain",
                "total_financial_gains",
                "approved_financial_gain",
                "approved_financial_gains",
                "ganho_financeiro",
                "ganhos_financeiros",
            ],
        ) or 0.0

        return {
            "department_id": "quality",
            "indicator_id": "quality-kaizen-financial",
            "value": value,
            "source": "quality_kaizen_financial",
            "unit_values": {"consolidated": value},
        }

    def _build_audit_5s_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = Audit5SSummaryRequest(
            start_date=start_date,
            end_date=end_date,
        )

        result = self._audit_5s_summary_use_case.execute(request)
        payload = result.to_dict() if hasattr(result, "to_dict") else result

        value = self._extract_first_number(
            payload,
            [
                "average_score",
                "avg_score",
                "score_average",
                "audit_score",
                "nota_media",
                "media",
                "average",
            ],
        ) or 0.0

        return {
            "department_id": "quality",
            "indicator_id": "quality-audit-5s",
            "value": value,
            "source": "quality_audit_5s",
            "unit_values": {"consolidated": value},
        }

    def _resolve_month_count(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> int:
        if not start_date or not end_date:
            return 1

        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        if not start or not end:
            return 1

        return ((end.year - start.year) * 12) + (end.month - start.month) + 1

    def _parse_date(self, value: str | None):
        if not value:
            return None

        from datetime import datetime

        known_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in known_formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def _extract_first_number(
        self,
        payload: dict,
        candidate_keys: list[str],
    ) -> float | None:
        for key in candidate_keys:
            value = payload.get(key)
            number = self._to_float(value)
            if number is not None:
                return number

        for value in payload.values():
            if isinstance(value, dict):
                found = self._extract_first_number(value, candidate_keys)
                if found is not None:
                    return found

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        found = self._extract_first_number(item, candidate_keys)
                        if found is not None:
                            return found

        return None

    def _to_float(self, value) -> float | None:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        raw = str(value).strip()
        if not raw:
            return None

        raw = raw.replace("R$", "").replace("%", "").replace(" ", "")

        if "," in raw and "." in raw:
            raw = raw.replace(".", "").replace(",", ".")
        elif "," in raw:
            raw = raw.replace(",", ".")

        try:
            return float(raw)
        except ValueError:
            return None