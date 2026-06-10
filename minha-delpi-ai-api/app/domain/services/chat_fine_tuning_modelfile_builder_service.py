"""Monta Modelfile Ollama a partir de amostras aprovadas (adaptador offline)."""

from __future__ import annotations

_MAX_EXAMPLES = 12
_MAX_EXAMPLE_CHARS = 280


class ChatFineTuningModelfileBuilderService:
    @staticmethod
    def build_model_name(*, dataset_id: int, run_id: int) -> str:
        return f"delpi-ft-d{dataset_id}-r{run_id}"

    @classmethod
    def build_modelfile(
        cls,
        *,
        base_model: str,
        samples: list[dict],
        target_model: str,
    ) -> str:
        base = str(base_model or "qwen2.5:3b").strip()
        lines = [f"FROM {base}", ""]
        system = cls._build_system_prompt(samples=samples, target_model=target_model)
        lines.append(f'SYSTEM """{system}"""')
        lines.append("")
        lines.append("PARAMETER temperature 0.35")
        lines.append("PARAMETER num_ctx 2048")
        return "\n".join(lines)

    @classmethod
    def _build_system_prompt(cls, *, samples: list[dict], target_model: str) -> str:
        role_hint = (
            "Você é o assistente Minha DELPI. Siga os exemplos validados abaixo "
            "ao responder perguntas semelhantes."
        )

        if str(target_model or "").strip() == "intent_classifier":
            role_hint = (
                "Você classifica intenções do chat Minha DELPI. "
                "Use os exemplos validados para orientar roteamento e respostas curtas."
            )

        examples: list[str] = []

        for sample in samples[:_MAX_EXAMPLES]:
            messages = sample.get("messages") or sample.get("messagesJson") or []

            if not isinstance(messages, list):
                continue

            user = cls._first_role_content(messages, "user")
            assistant = cls._first_role_content(messages, "assistant")

            if not user or not assistant:
                continue

            intent = sample.get("intentLabel") or sample.get("intent_label")
            intent_suffix = f" [intent={intent}]" if intent else ""
            examples.append(
                f"Usuário: {cls._trim(user)}\nAssistente{intent_suffix}: {cls._trim(assistant)}"
            )

        if not examples:
            return role_hint

        joined = "\n\n".join(examples)
        return f"{role_hint}\n\nExemplos validados:\n\n{joined}"

    @staticmethod
    def _first_role_content(messages: list, role: str) -> str | None:
        for item in messages:
            if not isinstance(item, dict):
                continue

            if str(item.get("role") or "").strip().lower() != role:
                continue

            content = str(item.get("content") or "").strip()

            if content:
                return content

        return None

    @staticmethod
    def _trim(text: str) -> str:
        compact = " ".join(str(text or "").split())

        if len(compact) <= _MAX_EXAMPLE_CHARS:
            return compact

        return compact[: _MAX_EXAMPLE_CHARS - 1].rstrip() + "…"
