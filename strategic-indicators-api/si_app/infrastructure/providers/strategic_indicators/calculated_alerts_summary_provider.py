from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
)
from si_app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
)
from si_app.application.services.strategic_indicators.measurements_cache_policy import (
    DEPARTMENT_LABELS,
    MISSING_DEPARTMENT_ERROR_CODE,
    format_measurement_errors_summary,
)
from si_app.shared.indicator_scoring import iter_scored_indicators


class CalculatedStrategicIndicatorsAlertsSummaryProvider(
    StrategicIndicatorsAlertsSummaryPort,
):
    def get_alerts_summary(
        self,
        *,
        departments: list[StrategicDepartmentCalculatedValue],
        measurement_errors: list[dict],
    ) -> list[dict]:
        alerts: list[dict] = []

        if not departments and measurement_errors:
            fetch_alert = self._build_measurement_error_alert(measurement_errors)
            if fetch_alert is not None:
                return [fetch_alert]
            return [
                {
                    "title": "Falha na coleta dos indicadores do período",
                    "severity": "high",
                    "impact": (
                        "Os dados disponíveis não foram suficientes para compor uma "
                        "leitura executiva confiável do período."
                    ),
                    "recommendation": (
                        "Validar integrações, planilhas e rotas operacionais antes de "
                        "tomar decisão baseada no painel."
                    ),
                }
            ]

        igd_alert = self._build_igd_band_alert(departments)
        if igd_alert is not None:
            alerts.append(igd_alert)

        department_alert = self._build_lowest_department_alert(departments)
        if department_alert is not None:
            alerts.append(department_alert)

        indicator_alert = self._build_department_indicator_risk_alert(departments)
        if indicator_alert is not None:
            alerts.append(indicator_alert)

        fetch_alert = self._build_measurement_error_alert(measurement_errors)
        if fetch_alert is not None:
            alerts.append(fetch_alert)

        return alerts[:3]

    def _build_igd_band_alert(
        self,
        departments: list[StrategicDepartmentCalculatedValue],
    ) -> dict | None:
        if not departments:
            return None

        weighted_sum = round(sum(item.contribution for item in departments), 3)
        igd = round(weighted_sum, 1)

        if igd < 6:
            return {
                "title": "IGD em faixa crítica",
                "severity": "high",
                "impact": (
                    "O índice global consolidado indica deterioração relevante do "
                    "desempenho estratégico."
                ),
                "recommendation": (
                    "Priorizar rapidamente as áreas com menor score e revisar "
                    "indicadores abaixo da meta crítica."
                ),
            }

        if igd < 7:
            return {
                "title": "IGD exige ação gerencial",
                "severity": "high",
                "impact": (
                    "O desempenho global está abaixo da faixa satisfatória e pode "
                    "comprometer a estabilidade do ciclo."
                ),
                "recommendation": (
                    "Atacar primeiro departamentos com score abaixo de 7,0 e "
                    "indicadores com maior peso."
                ),
            }

        if igd < 8:
            return {
                "title": "IGD em faixa de atenção",
                "severity": "medium",
                "impact": (
                    "O índice global permanece em faixa satisfatória, porém ainda "
                    "com alertas relevantes."
                ),
                "recommendation": (
                    "Concentrar esforços nos departamentos com menor score e nos "
                    "indicadores mais distantes da meta."
                ),
            }

        return None

    def _build_lowest_department_alert(
        self,
        departments: list[StrategicDepartmentCalculatedValue],
    ) -> dict | None:
        if not departments:
            return None

        lowest = min(departments, key=lambda item: item.score)

        if lowest.score >= 8:
            return None

        severity = "high" if lowest.score < 7 else "medium"

        return {
            "title": f"{lowest.department_name} é o principal foco do período",
            "severity": severity,
            "impact": (
                f"O departamento apresenta score {lowest.score:.1f}, o menor entre "
                "as áreas avaliadas no fechamento atual."
            ),
            "recommendation": (
                "Revisar os indicadores de maior peso da área e construir plano de "
                "ação com responsáveis e prazo curto."
            ),
        }

    def _build_department_indicator_risk_alert(
        self,
        departments: list[StrategicDepartmentCalculatedValue],
    ) -> dict | None:
        candidates: list[tuple[StrategicDepartmentCalculatedValue, object]] = []

        for department in departments:
            scored_indicators = iter_scored_indicators(department.indicators)
            if not scored_indicators:
                continue

            worst_indicator = min(scored_indicators, key=lambda item: item.score)
            candidates.append((department, worst_indicator))

        if not candidates:
            return None

        department, indicator = min(candidates, key=lambda item: item[1].score)

        indicator_score = float(indicator.score)
        indicator_gap = float(indicator.gap or 0)

        if indicator_score >= 7:
            return None

        severity = "high" if indicator_score < 6 else "medium"

        return {
            "title": f"Risco concentrado em {indicator.indicator_name}",
            "severity": severity,
            "impact": (
                f"O indicador crítico está em {department.department_name}, com "
                f"score {indicator_score:.1f} e gap {indicator_gap:.2f}."
            ),
            "recommendation": (
                "Atuar diretamente na causa operacional do indicador e monitorar sua "
                "evolução no próximo fechamento."
            ),
        }

    def _build_measurement_error_alert(
        self,
        measurement_errors: list[dict],
    ) -> dict | None:
        if not measurement_errors:
            return None

        missing_departments = sorted(
            {
                str(item.get("department_id") or "").strip()
                for item in measurement_errors
                if item.get("code") == MISSING_DEPARTMENT_ERROR_CODE
                and item.get("department_id")
            }
        )
        fetch_failures = [
            item
            for item in measurement_errors
            if item.get("code") != MISSING_DEPARTMENT_ERROR_CODE
        ]

        if missing_departments and len(missing_departments) >= 3:
            severity = "high"
            title = "Coleta incompleta — vários departamentos sem medições"
        elif measurement_errors:
            severity = "high" if len(measurement_errors) >= 3 else "medium"
            title = "Falhas na coleta de indicadores do período"
        else:
            return None

        missing_labels = [
            DEPARTMENT_LABELS.get(dept_id, dept_id) for dept_id in missing_departments
        ]
        impact_parts: list[str] = []

        if missing_labels:
            impact_parts.append(
                "Departamentos sem medições no período: "
                + ", ".join(missing_labels)
                + ". O IGD pode aparecer próximo de zero nessas áreas."
            )

        if fetch_failures:
            impact_parts.append(
                "Detalhes das falhas de integração:\n"
                + format_measurement_errors_summary(fetch_failures, limit=6)
            )
        elif not missing_labels:
            impact_parts.append(
                "Detalhes:\n"
                + format_measurement_errors_summary(measurement_errors, limit=8)
            )

        return {
            "title": title,
            "severity": severity,
            "impact": "\n\n".join(impact_parts),
            "recommendation": (
                "Aguarde o término do refresh materializado ou execute "
                "`refresh_period_scores` após validar api-delpi e planilhas. "
                "Recarregue o painel em seguida."
            ),
        }