class ChatLearningMetricsService:
    """Monta KPIs de aprendizagem progressiva (playbook §36). Puro/sem DB."""

    @staticmethod
    def assemble(
        *,
        candidates: dict,
        vocabulary: dict,
        memory: dict | None = None,
        evaluation: dict | None = None,
        fine_tuning: dict | None = None,
    ) -> dict:
        by_status = candidates.get("byStatus", {}) if isinstance(candidates, dict) else {}

        pending = int(by_status.get("pending", 0)) + int(by_status.get("auto_approved", 0))
        approved = int(by_status.get("approved", 0))
        promoted = int(by_status.get("promoted", 0))
        rejected = int(by_status.get("rejected", 0))

        reviewed = approved + promoted + rejected
        approval_rate = round((approved + promoted) / reviewed, 4) if reviewed else None
        promotion_rate = (
            round(promoted / int(candidates.get("total", 0)), 4)
            if int(candidates.get("total", 0)) > 0
            else None
        )

        by_type = candidates.get("byType", {}) if isinstance(candidates, dict) else {}
        memory = memory if isinstance(memory, dict) else {"total": 0, "active": 0}
        evaluation = evaluation if isinstance(evaluation, dict) else {"total": 0, "failing": 0}
        fine_tuning = fine_tuning if isinstance(fine_tuning, dict) else {}

        return {
            "candidates": candidates,
            "vocabulary": vocabulary,
            "memory": memory,
            "evaluation": evaluation,
            "fineTuning": fine_tuning,
            "funnel": {
                "created": int(candidates.get("total", 0)),
                "recentCreated": int(candidates.get("recentCreated", 0)),
                "pending": pending,
                "approved": approved + promoted,
                "rejected": rejected,
                "promoted": promoted,
                "approvalRate": approval_rate,
                "promotionRate": promotion_rate,
            },
            "highlights": {
                "termDefinitions": int(by_type.get("term_definition", 0)),
                "normalizationRules": int(by_type.get("normalization_rule", 0)),
                "pendingHighConfidence": int(candidates.get("pendingHighConfidence", 0)),
                "learnedTermsActive": int(vocabulary.get("activeApproved", 0))
                if isinstance(vocabulary, dict)
                else 0,
                "memoryItemsActive": int(memory.get("active", 0)),
                "evaluationCasesFailing": int(evaluation.get("failing", 0)),
                "evaluationCasesActive": int(evaluation.get("active", 0)),
                "fineTuningSamplesApproved": int(fine_tuning.get("samplesApproved", 0)),
                "fineTuningDatasetsApproved": int(fine_tuning.get("datasetsApproved", 0)),
            },
        }
