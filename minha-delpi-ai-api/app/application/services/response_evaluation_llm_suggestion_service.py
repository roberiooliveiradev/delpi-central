import json
import re

from app.infrastructure.config.settings import Settings


class ResponseEvaluationLlmSuggestionService:
    def __init__(self, llm_gateway=None):
        self.llm_gateway = llm_gateway

    def enrich_suggestions(
        self,
        *,
        base_suggestions: dict,
        score: int,
        verdict: str,
        user_question: str | None,
        assistant_answer: str,
    ) -> dict:
        if not self.llm_gateway or not Settings.RESPONSE_EVALUATION_LLM_SUGGESTIONS_ENABLED:
            return base_suggestions

        prompt = self._build_prompt(
            score=score,
            verdict=verdict,
            user_question=user_question,
            assistant_answer=assistant_answer,
            base_suggestions=base_suggestions,
        )

        try:
            raw = self.llm_gateway.generate(
                [
                    {
                        "role": "system",
                        "content": (
                            "Você é um revisor de qualidade do Minha DELPI Chat. "
                            "Responda apenas JSON válido."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            parsed = self._parse_json(raw)

            if not isinstance(parsed, dict):
                return base_suggestions

            merged = dict(base_suggestions)
            llm_notes = parsed.get("notes")

            if isinstance(llm_notes, list):
                merged.setdefault("notes", [])
                merged["notes"].extend(
                    [note for note in llm_notes if isinstance(note, dict)]
                )

            llm_documents = parsed.get("documents")

            if isinstance(llm_documents, list):
                merged.setdefault("documents", [])
                merged["documents"].extend(
                    [item for item in llm_documents if isinstance(item, dict)]
                )

            llm_guidelines = parsed.get("guidelines")

            if isinstance(llm_guidelines, list):
                merged.setdefault("guidelines", [])
                merged["guidelines"].extend(
                    [item for item in llm_guidelines if isinstance(item, dict)]
                )

            merged["llmGenerated"] = True
            return merged
        except Exception:
            return base_suggestions

    def _build_prompt(
        self,
        *,
        score: int,
        verdict: str,
        user_question: str | None,
        assistant_answer: str,
        base_suggestions: dict,
    ) -> str:
        return (
            "Analise a resposta do assistente e sugira melhorias em conhecimento/diretrizes.\n"
            f"Score: {score}\n"
            f"Veredito: {verdict}\n"
            f"Pergunta: {user_question or '(não identificada)'}\n"
            f"Resposta: {assistant_answer[:1200]}\n"
            f"Sugestões base (regras): {json.dumps(base_suggestions, ensure_ascii=False)[:2000]}\n"
            "Retorne JSON: {\"documents\":[],\"guidelines\":[],\"notes\":[]}"
        )

    def _parse_json(self, raw: str) -> dict | list | None:
        text = str(raw or "").strip()

        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)

            if not match:
                return None

            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
