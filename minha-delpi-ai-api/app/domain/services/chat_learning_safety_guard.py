from app.domain.services.chat_learning_content_service import ChatLearningContentService


class ChatLearningSafetyGuard:
    """Bloqueia aprendizado tóxico/sensível (playbook §26 — ChatLearningSafetyGuard)."""

    @classmethod
    def inspect(cls, text: str, *, candidate_type: str | None = None) -> dict:
        """Retorna {allowed, riskLevel, reason} para um texto candidato."""
        content = str(text or "").strip()

        if not content:
            return {
                "allowed": False,
                "riskLevel": ChatLearningContentService.risk_level("high"),
                "reason": ChatLearningContentService.safety_reason("empty"),
            }

        for pattern in ChatLearningContentService.compile_pattern_list("secretPatterns"):
            if pattern.search(content):
                return {
                    "allowed": False,
                    "riskLevel": ChatLearningContentService.risk_level("high"),
                    "reason": ChatLearningContentService.safety_reason("secret_detected"),
                }

        for pattern in ChatLearningContentService.compile_pattern_list("piiPatterns"):
            if pattern.search(content):
                return {
                    "allowed": False,
                    "riskLevel": ChatLearningContentService.risk_level("high"),
                    "reason": ChatLearningContentService.safety_reason("pii_detected"),
                }

        digit_check_types = {
            str(item)
            for item in ChatLearningContentService.list(
                "patternLists",
                "safetyDigitCheckCandidateTypes",
            )
        }

        if candidate_type in digit_check_types:
            if ChatLearningContentService.compile_pattern("longDigitRun").search(content):
                return {
                    "allowed": False,
                    "riskLevel": ChatLearningContentService.risk_level("medium"),
                    "reason": ChatLearningContentService.safety_reason("operational_code"),
                }

        for pattern in ChatLearningContentService.compile_pattern_list(
            "operationalSensitivePatterns"
        ):
            if pattern.search(content):
                return {
                    "allowed": False,
                    "riskLevel": ChatLearningContentService.risk_level("medium"),
                    "reason": ChatLearningContentService.safety_reason("operational_sensitive"),
                }

        return {
            "allowed": True,
            "riskLevel": ChatLearningContentService.risk_level("low"),
            "reason": None,
        }

    @classmethod
    def is_safe_to_learn(cls, text: str, *, candidate_type: str | None = None) -> bool:
        return cls.inspect(text, candidate_type=candidate_type)["allowed"]
