from __future__ import annotations

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
)
from app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
)


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
            if not department.indicators:
                continue

            worst_indicator = min(department.indicators, key=lambda item: item.score)
            candidates.append((department, worst_indicator))

        if not candidates:
            return None

        department, indicator = min(candidates, key=lambda item: item[1].score)

        if indicator.score >= 7:
            return None

        severity = "high" if indicator.score < 6 else "medium"

        return {
            "title": f"Risco concentrado em {indicator.indicator_name}",
            "severity": severity,
            "impact": (
                f"O indicador crítico está em {department.department_name}, com "
                f"score {indicator.score:.1f} e gap {indicator.gap:.2f}."
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

        affected_departments = sorted(
            {item["department_id"] for item in measurement_errors if item.get("department_id")}
        )
        affected_sources = sorted(
            {item["source"] for item in measurement_errors if item.get("source")}
        )

        departments_label = ", ".join(affected_departments) if affected_departments else "módulo"
        sources_label = ", ".join(affected_sources[:3]) if affected_sources else "fontes"

        return {
            "title": "Parte das fontes falhou na coleta do período",
            "severity": "medium",
            "impact": (
                f"Foram identificadas falhas parciais em {departments_label}, o que "
                f"pode reduzir a cobertura analítica do painel."
            ),
            "recommendation": (
                f"Validar as fontes {sources_label} e repetir a leitura após corrigir "
                "as integrações com erro."
            ),
        }