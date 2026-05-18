import json
import os

from app.application.services.llm_cost_estimator_service import LlmCostEstimatorService


def test_estimate_cost_from_table_entry(monkeypatch):
    table = [
        {
            "provider": "vllm",
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "promptCostPer1k": 0.1,
            "completionCostPer1k": 0.2,
            "currency": "BRL",
        }
    ]
    monkeypatch.setenv("LLM_COST_TABLE_JSON", json.dumps(table))

    service = LlmCostEstimatorService()

    cost = service.estimate_cost(
        provider="vllm",
        model="Qwen/Qwen2.5-7B-Instruct",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    assert cost == 0.2


def test_list_cost_table_uses_env_json(monkeypatch):
    table = [
        {
            "provider": "ollama",
            "model": "qwen2.5:1.5b",
            "promptCostPer1k": 0,
            "completionCostPer1k": 0,
            "currency": "BRL",
        }
    ]
    monkeypatch.setenv("LLM_COST_TABLE_JSON", json.dumps(table))

    service = LlmCostEstimatorService()

    assert len(service.list_cost_table()) == 1
    assert service.list_cost_table()[0]["provider"] == "ollama"
