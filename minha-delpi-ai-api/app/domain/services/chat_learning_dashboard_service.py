"""Enriquecimento de KPIs do painel de aprendizagem (playbook §36–§37)."""


class ChatLearningDashboardService:
    @staticmethod
    def enrich(
        *,
        summary: dict,
        rag_index_counts: dict | None = None,
        top_typo_rules: list[dict] | None = None,
    ) -> dict:
        if not isinstance(summary, dict):
            return summary

        rag = rag_index_counts if isinstance(rag_index_counts, dict) else {}
        typos = top_typo_rules if isinstance(top_typo_rules, list) else []

        summary["ragIndex"] = {
            "glossaryDocuments": int(rag.get("glossary", 0)),
            "userMemoryDocuments": int(rag.get("user_memory", 0)),
        }

        summary["dashboard"] = {
            "topTypoRules": [
                {
                    "term": str(item.get("term") or ""),
                    "normalizedTerm": str(item.get("normalizedTerm") or ""),
                    "evidenceCount": int(item.get("evidenceCount") or 0),
                }
                for item in typos[:8]
                if isinstance(item, dict)
            ],
        }

        highlights = dict(summary.get("highlights") or {})
        highlights["ragGlossaryIndexed"] = int(rag.get("glossary", 0))
        highlights["ragUserMemoryIndexed"] = int(rag.get("user_memory", 0))
        summary["highlights"] = highlights

        return summary
