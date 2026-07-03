from __future__ import annotations

import json
import logging

import requests

from app.domain.ports.fine_tuning_model_gateway_port import FineTuningModelGatewayPort
from app.infrastructure.config.llm_text_config import resolve_llm_text_config


logger = logging.getLogger("minha-delpi-ai-api.fine-tuning.ollama")


class OllamaFineTuningModelGateway(FineTuningModelGatewayPort):
    def __init__(self):
        config = resolve_llm_text_config()
        self.base_url = config.base_url.rstrip("/")
        self.timeout = config.timeout_seconds

    def supports_local_deploy(self) -> bool:
        return True

    def provider_name(self) -> str:
        return "ollama"

    def create_from_modelfile(self, *, name: str, modelfile: str) -> dict:
        url = f"{self.base_url}/api/create"
        payload = {"name": str(name).strip(), "modelfile": modelfile, "stream": True}

        try:
            with requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                stream=True,
            ) as response:
                response.raise_for_status()
                last_status = None

                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue

                    try:
                        data = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue

                    last_status = data.get("status")

                    if data.get("error"):
                        raise RuntimeError(str(data.get("error")))

                if last_status and "success" not in str(last_status).lower():
                    logger.info("ollama_create_finished status=%s", last_status)

                return {"model": name, "status": last_status or "success"}
        except requests.RequestException as exc:
            logger.exception("ollama_create_failed model=%s", name)
            raise RuntimeError(f"Ollama create failed for {name}") from exc
