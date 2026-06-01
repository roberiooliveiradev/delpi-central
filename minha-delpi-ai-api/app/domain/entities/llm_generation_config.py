from dataclasses import dataclass


@dataclass(frozen=True)
class LlmGenerationConfig:
    """Parâmetros efetivos de uma chamada LLM (por modo de resposta do chat)."""

    model: str
    max_tokens: int
    num_ctx: int
    temperature: float
    response_mode: str = "normal"
