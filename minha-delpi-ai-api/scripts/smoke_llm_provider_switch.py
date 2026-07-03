#!/usr/bin/env python3
"""Smoke local — wiring de providers LLM (sem chamada HTTP real)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.composition.provider_registry import resolve_llm_gateway_factory


def _assert_gateway(provider: str, expected_class_name: str) -> None:
    gateway = resolve_llm_gateway_factory(provider)()
    actual = gateway.__class__.__name__

    if actual != expected_class_name:
        raise RuntimeError(
            f"provider={provider} esperava {expected_class_name}, obteve {actual}"
        )

    print(f"OK provider={provider} gateway={actual}")


def main() -> int:
    _assert_gateway("ollama", "OllamaLlmGateway")
    _assert_gateway("vllm", "OpenAiCompatibleLlmGateway")
    _assert_gateway("openai_compatible", "OpenAiCompatibleLlmGateway")
    _assert_gateway("openai", "OpenAiCompatibleLlmGateway")
    print("smoke_llm_provider_switch: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
