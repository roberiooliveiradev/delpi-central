"""Síntese estruturada (LLM) de múltiplos resultados de web_search."""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_web_search_direct_answer_service import (
    ChatWebSearchDirectAnswerService,
)
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.web_search")


class ChatWebSearchSynthesisService:
    def __init__(self, llm_gateway: LlmGatewayPort | None = None):
        self.llm_gateway = llm_gateway

    def is_enabled(self) -> bool:
        return (
            Settings.CHAT_WEB_SEARCH_SYNTHESIS_ENABLED
            and Settings.CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED
            and self.llm_gateway is not None
        )

    def should_synthesize(self, payload: dict | None) -> bool:
        if not self.is_enabled() or not isinstance(payload, dict):
            return False

        if str(payload.get("searchStatus") or "") != "success":
            return False

        useful = ChatWebSearchDirectAnswerService.extract_useful_results(payload)
        minimum = max(1, int(Settings.CHAT_WEB_SEARCH_SYNTHESIS_MIN_RESULTS))

        return len(useful) >= minimum

    def synthesize(
        self,
        payload: dict,
        *,
        message: str = "",
        fallback: str | None = None,
    ) -> str | None:
        if not self.should_synthesize(payload):
            return fallback

        assert self.llm_gateway is not None

        query = str(payload.get("query") or message or "").strip()
        sources_block = self._build_sources_block(payload)
        user_question = str(message or query or "Consulta web").strip()

        try:
            raw = self.llm_gateway.generate(
                [
                    {"role": "system", "content": self._system_prompt()},
                    {
                        "role": "user",
                        "content": (
                            f"Pergunta do usuário: {user_question}\n"
                            f"Consulta executada na web: {query or 'n/d'}\n\n"
                            f"Trechos autorizados da busca:\n{sources_block}"
                        ),
                    },
                ]
            )
        except Exception as exc:
            logger.warning("Síntese web_search falhou; usando resposta simples: %s", exc)
            return fallback

        answer = self._normalize_answer(str(raw or "").strip())

        if not answer or len(answer) < 80:
            return fallback

        return answer

    @classmethod
    def _system_prompt(cls) -> str:
        return (
            "Você resume resultados de busca na internet pública para usuários da DELPI.\n"
            "Regras:\n"
            "- Escreva em português brasileiro claro e profissional.\n"
            "- Use SOMENTE fatos presentes nos trechos fornecidos; não invente URLs, datas ou empresas.\n"
            "- Estrutura sugerida (adapte ao conteúdo disponível):\n"
            "  1) Introdução curta contextualizando o tema.\n"
            "  2) Seções numeradas (### 1. Título) quando houver linhas/contextos distintos "
            "(ex.: empresas homônimas, divisões históricas).\n"
            "  3) Tabela markdown «Linha do tempo resumida» com colunas | Ano | Evento | "
            "quando houver datas nos trechos.\n"
            "  4) Seção «Conclusão prática» com orientação objetiva.\n"
            "- Ao final de parágrafos ou seções, cite fontes com links markdown compactos "
            "no formato [Nome curto](url) usando APENAS URLs fornecidas.\n"
            "- Não diga que não pesquisa na internet; a busca já foi feita.\n"
            "- Não inclua bloco de código; responda só markdown."
        )

    @classmethod
    def _build_sources_block(cls, payload: dict) -> str:
        useful = ChatWebSearchDirectAnswerService.extract_useful_results(payload)
        lines: list[str] = []

        for index, item in enumerate(useful[:8], start=1):
            title = str(item.get("title") or f"Fonte {index}").strip()
            snippet = " ".join(str(item.get("snippet") or "").split())
            url = str(item.get("url") or "").strip()
            label = cls._source_label(title, url)

            lines.append(f"[{index}] {label}")
            lines.append(f"URL: {url or 'sem url'}")
            lines.append(f"Trecho: {snippet[:900]}")
            lines.append("")

        return "\n".join(lines).strip() or "Sem trechos."

    @classmethod
    def _source_label(cls, title: str, url: str) -> str:
        cleaned = str(title or "").strip()

        if len(cleaned) > 56:
            cleaned = cls._hostname(url) or cleaned[:56]

        return cleaned or cls._hostname(url) or "Fonte"

    @classmethod
    def _hostname(cls, url: str) -> str:
        hostname = urlparse(str(url or "").strip()).hostname or ""

        if hostname.startswith("www."):
            return hostname[4:]

        return hostname

    @classmethod
    def _normalize_answer(cls, answer: str) -> str:
        value = answer.strip()

        if value.startswith("```"):
            value = re.sub(r"^```(?:markdown|md)?\s*", "", value, flags=re.IGNORECASE)
            value = re.sub(r"\s*```$", "", value).strip()

        return value

    def enhance_prepared_turn(
        self,
        *,
        message: str,
        tool_context: dict | None,
        direct_answer: str | None,
        pipeline_stages: list[str],
    ) -> tuple[str | None, list[str]]:
        payload = tool_context.get("webSearchPayload") if isinstance(tool_context, dict) else None

        if not payload or not direct_answer:
            return direct_answer, pipeline_stages

        synthesized = self.synthesize(payload, message=message, fallback=direct_answer)
        stages = list(pipeline_stages)

        if synthesized and synthesized != direct_answer:
            if "web_search_synthesis" not in stages:
                stages.append("web_search_synthesis")

            return synthesized, stages

        return direct_answer, stages
