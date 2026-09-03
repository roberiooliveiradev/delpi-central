"""Stack LLM canônico — um seletor, três eixos.

Troca de motor: ``LLM_PROVIDER`` (``ollama`` | ``openai_compatible``; aliases ``vllm``/``openai``).

Eixos (herdam o seletor quando o env do eixo está vazio):

- texto — ``make_llm_gateway()`` / ``resolve_llm_text_config()``
- embeddings — ``make_embedding_gateway()`` / ``resolve_embedding_config()``
- visão — ``make_vision_llm_gateway()`` / ``resolve_vision_llm_config()``

Não chamar host Ollama (``http://ollama:11434``) a partir de use case, vision stage ou RAG.
O gateway de infra só é construído quando o provedor efetivo é ``ollama``.
"""

from __future__ import annotations

import os
from collections.abc import Callable


def env_stripped(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def resolve_inherited_provider(
    explicit_env_name: str,
    *,
    normalize: Callable[[str], str],
    stack_provider: str,
) -> str:
    explicit = env_stripped(explicit_env_name)
    if explicit:
        return normalize(explicit)
    return normalize(stack_provider)
