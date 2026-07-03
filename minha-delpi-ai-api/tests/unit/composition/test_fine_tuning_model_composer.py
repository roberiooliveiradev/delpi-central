from unittest.mock import MagicMock, patch

import pytest

from app.composition.fine_tuning_model_composer import make_fine_tuning_model_gateway
from app.infrastructure.llm.export_only_fine_tuning_model_gateway import (
    ExportOnlyFineTuningModelGateway,
)
from app.infrastructure.llm.ollama_fine_tuning_model_gateway import OllamaFineTuningModelGateway


def test_make_fine_tuning_model_gateway_ollama(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    gateway = make_fine_tuning_model_gateway()
    assert isinstance(gateway, OllamaFineTuningModelGateway)
    assert gateway.supports_local_deploy() is True


def test_make_fine_tuning_model_gateway_export_only(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    gateway = make_fine_tuning_model_gateway()
    assert isinstance(gateway, ExportOnlyFineTuningModelGateway)
    assert gateway.supports_local_deploy() is False


def test_ollama_gateway_create_from_modelfile(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    gateway = OllamaFineTuningModelGateway()

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.iter_lines.return_value = iter(['{"status":"success"}'])
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch(
        "app.infrastructure.llm.ollama_fine_tuning_model_gateway.requests.post",
        return_value=response,
    ):
        result = gateway.create_from_modelfile(name="delpi-ft-test", modelfile="FROM qwen2.5:3b")

    assert result["model"] == "delpi-ft-test"
