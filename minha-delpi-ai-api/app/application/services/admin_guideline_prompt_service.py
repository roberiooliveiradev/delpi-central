class AdminGuidelinePromptService:
    def __init__(self, guideline_repository):
        self.guideline_repository = guideline_repository

    def build_active_guidelines_prompt(self) -> tuple[str, list[dict]]:
        guidelines = self.guideline_repository.list_active()

        if not guidelines:
            return "", []

        lines = [
            "Diretrizes administrativas globais ativas:",
            "Estas regras foram definidas pela administração do Minha DELPI Chat e devem ser obedecidas em todas as respostas.",
        ]

        for index, guideline in enumerate(guidelines, start=1):
            title = self._clean(guideline.get("title"))
            category = self._clean(guideline.get("category"))
            content = self._clean(guideline.get("content"))
            description = self._clean(guideline.get("description"))

            if not content:
                continue

            heading = f"{index}. {title}"
            if category:
                heading = f"{heading} [{category}]"

            lines.append(heading)

            if description:
                lines.append(f"Resumo: {description}")

            lines.append(f"Regra: {content}")

        if len(lines) <= 2:
            return "", []

        return "\\n".join(lines), guidelines

    def _clean(self, value) -> str:
        return " ".join(str(value or "").split())
