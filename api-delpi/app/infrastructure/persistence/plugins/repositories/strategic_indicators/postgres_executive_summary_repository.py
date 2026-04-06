from __future__ import annotations

from datetime import date

from app.domain.ports.strategic_indicators.executive_summary_repository_port import (
    StrategicIndicatorsExecutiveSummaryRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsExecutiveSummaryRepository(
    PluginBaseRepository,
    StrategicIndicatorsExecutiveSummaryRepositoryPort,
):
    OFFICIAL_EXECUTIVE_SCORES = {
        "financial": {
            "score": 7.8,
            "contribution": 1.17,
            "trend": "up",
            "short_name": "FIN",
            "strategic_summary": (
                "Geração de resultado operacional, eficiência da estrutura e "
                "fluxo de caixa."
            ),
            "key_indicators": [
                "EBITDA / Receita Operacional",
                "% Custos Fixos / Receita Operacional",
                "Prazo Médio de Recebimento (PMR)",
            ],
        },
        "hr": {
            "score": 8.0,
            "contribution": 1.2,
            "trend": "up",
            "short_name": "RH",
            "strategic_summary": (
                "Engajamento, retenção, desenvolvimento individual e "
                "capacitação contínua."
            ),
            "key_indicators": [
                "Absenteísmo",
                "Turnover",
                "Satisfação Interna",
            ],
        },
        "commercial": {
            "score": 8.2,
            "contribution": 1.394,
            "trend": "up",
            "short_name": "COM",
            "strategic_summary": (
                "Receita, conversão de negócios e expansão da base de clientes."
            ),
            "key_indicators": [
                "ROL Matriz / Meta",
                "Taxa de Fechamento de Negócios",
                "Número de Novos Clientes",
            ],
        },
        "production": {
            "score": 7.8,
            "contribution": 1.326,
            "trend": "up",
            "short_name": "PRD",
            "strategic_summary": (
                "Eficiência produtiva, uso dos ativos e cumprimento do prazo "
                "ao cliente."
            ),
            "key_indicators": [
                "Custo MOD / ROL",
                "OEE",
                "OTD",
            ],
        },
        "quality": {
            "score": 7.4,
            "contribution": 1.036,
            "trend": "up",
            "short_name": "QLD",
            "strategic_summary": (
                "Falhas internas e externas, disciplina operacional e ganhos "
                "com melhoria contínua."
            ),
            "key_indicators": [
                "PPM Interno",
                "PPM Externo",
                "Nota Auditoria 5S",
            ],
        },
        "supplies": {
            "score": 7.1,
            "contribution": 0.852,
            "trend": "down",
            "short_name": "SUP",
            "strategic_summary": (
                "Eficiência em compras, estoque e negociações com fornecedores."
            ),
            "key_indicators": [
                "CPV Consolidado",
                "OTD Compras",
                "Giro de Estoque",
            ],
        },
        "engineering": {
            "score": 7.9,
            "contribution": 0.79,
            "trend": "up",
            "short_name": "ENG",
            "strategic_summary": (
                "Entrega no prazo e geração de valor via inovação e "
                "digitalização."
            ),
            "key_indicators": [
                "% Projetos Concluídos no Prazo",
                "Ganhos Financeiros do TRANSFORMA+ DELPI",
            ],
        },
    }

    ALERTS_SUMMARY = [
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

    def get_executive_summary(self) -> dict:
        settings = self._get_settings_payloads()

        weights_items = settings["weights"].get("items", [])
        goals_items = settings["goals"].get("items", [])

        goals_map = {
            item["department_id"]: item["headline_goal"]
            for item in goals_items
            if item.get("department_id") and item.get("headline_goal")
        }

        departments = []
        for item in weights_items:
            department_id = item["department_id"]
            baseline = self.OFFICIAL_EXECUTIVE_SCORES.get(department_id)

            if baseline is None:
                continue

            departments.append(
                {
                    "id": department_id,
                    "name": item["department_name"],
                    "short_name": baseline["short_name"],
                    "weight_pct": item["weight_pct"],
                    "score": baseline["score"],
                    "contribution": baseline["contribution"],
                    "trend": baseline["trend"],
                    "strategic_summary": baseline["strategic_summary"],
                    "key_indicators": baseline["key_indicators"],
                    "executive_goal": goals_map.get(department_id, ""),
                }
            )

        return {
            "competence": date.today().strftime("%Y-%m"),
            "igd": 7.8,
            "igd_exact": 7.768,
            "classification": "Satisfatório com Alertas",
            "variation": {
                "value": 0.2,
                "direction": "up",
                "vs_label": "vs período anterior",
            },
            "departments": departments,
            "alerts_summary": self.ALERTS_SUMMARY,
        }

    def _get_settings_payloads(self) -> dict:
        query = """
            SELECT
                setting_key,
                payload_json
            FROM strategic_indicators.module_settings
            WHERE is_active = TRUE
              AND setting_key IN (
                'weights.departments',
                'goals.summary'
              )
        """

        rows = self.fetch_all(query)

        result = {
            "weights": {"items": []},
            "goals": {"items": []},
        }

        for row in rows:
            setting_key = row["setting_key"]
            payload = row.get("payload_json") or {"items": []}

            if setting_key == "weights.departments":
                result["weights"] = payload
            elif setting_key == "goals.summary":
                result["goals"] = payload

        return result