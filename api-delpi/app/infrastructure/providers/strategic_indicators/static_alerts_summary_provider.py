from __future__ import annotations

from app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
)


class StaticStrategicIndicatorsAlertsSummaryProvider(
    StrategicIndicatorsAlertsSummaryPort
):
    def get_alerts_summary(self) -> list[dict]:
        return [
            {
                "title": "IGD em faixa de atenção",
                "severity": "medium",
                "impact": (
                    "O índice global permanece em faixa satisfatória, porém ainda "
                    "com alertas."
                ),
                "recommendation": (
                    "Priorizar departamentos com queda recente e indicadores abaixo "
                    "da meta crítica."
                ),
            },
            {
                "title": "Suprimentos apresentou queda no período",
                "severity": "high",
                "impact": (
                    "A redução recente impacta a estabilidade do IGD e aumenta "
                    "risco operacional."
                ),
                "recommendation": (
                    "Revisar estoque consolidado, desempenho de compras e "
                    "eficiência das negociações."
                ),
            },
            {
                "title": "Qualidade com risco em falhas externas",
                "severity": "high",
                "impact": (
                    "Indicadores de falha percebida pelo cliente afetam imagem e "
                    "confiabilidade."
                ),
                "recommendation": (
                    "Atacar PPM Externo com plano de contenção e reforço de análise "
                    "de causa."
                ),
            },
        ]