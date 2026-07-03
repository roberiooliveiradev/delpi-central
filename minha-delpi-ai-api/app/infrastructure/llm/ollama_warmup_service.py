from app.infrastructure.llm.llm_warmup_service import warmup_llm_on_startup

warmup_ollama = warmup_llm_on_startup

__all__ = ["warmup_ollama", "warmup_llm_on_startup"]
