"""Gateway Kimi (OpenAI-compatible) para geração de seções de ata Transforma+.

Padrão adaptado de ``OpenAiCompatibleLlmGateway`` (minha-delpi-ai-api):
HTTP via ``requests`` + exceção de domínio clara — sem vazar traceback cru ao cliente.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from tm_app.config import settings

logger = logging.getLogger("transformometro.llm.kimi")

REQUIRED_SECTION_KEYS = (
    "agenda_html",
    "body_html",
    "decisions_html",
    "pending_html",
    "observations_html",
)

DEFAULT_TIMEOUT_SECONDS = 180
# Texto puro enviado ao modelo (após strip de HTML). 20k cobre reunião longa sem estourar latência.
DEFAULT_MAX_TRANSCRIPT_CHARS = 20_000
DEFAULT_MAX_OUTPUT_TOKENS = 4_096

SYSTEM_PROMPT = """
Você é um assistente que gera atas de reunião formais a partir de transcrições
do projeto Transforma+ / Transformômetro (Delpi).

Regras obrigatórias:
1. Responda APENAS com um único objeto JSON válido (sem markdown, sem texto fora do JSON).
2. O JSON deve conter EXATAMENTE estas chaves (todas strings HTML):
   - agenda_html
   - body_html
   - decisions_html
   - pending_html
   - observations_html
3. Use HTML simples adequado a um editor rich-text: <p>, <ul>, <ol>, <li>, <strong>, <em>, <br>
   e, quando a transcrição trouxer grades/listagens tabulares, <table>/<thead>/<tbody>/<tr>/<th>/<td>
   (sem scripts, sem <style> global e sem imagens).
4. agenda_html: pauta / assuntos tratados.
5. body_html: narrativa do andamento da reunião (discussão).
6. decisions_html: decisões tomadas.
7. pending_html: pendências e responsáveis/prazos quando houver.
8. observations_html: observações finais, próximos encontros, etc.
9. Se a transcrição não trouxer material para uma seção, use um parágrafo curto
   indicando que não houve itens relevantes (ainda assim a chave deve existir).
10. Escreva em português do Brasil, tom formal e objetivo.
11. Seja conciso: body_html em poucos parágrafos; listas curtas nas demais seções.
""".strip()


class AtaGenerationError(Exception):
    """Falha ao gerar seções de ata via provedor LLM (Kimi / OpenAI-compatible)."""


def _strip_markdown_fences(content: str) -> str:
    text = content.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (requests.Timeout, TimeoutError)):
        return True
    message = str(exc).lower()
    return "timed out" in message or "timeout" in message


def _html_to_plain_text(transcript_html: str) -> str:
    """Remove tags/HTML entities — o modelo precisa do conteúdo, não do markup."""
    import html as html_lib
    import re
    from html.parser import HTMLParser

    class _Extractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.parts: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag in {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "blockquote", "table"}:
                self.parts.append("\n")
            elif tag in {"td", "th"}:
                self.parts.append(" | ")

        def handle_endtag(self, tag: str) -> None:
            if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "blockquote", "table"}:
                self.parts.append("\n")

        def handle_data(self, data: str) -> None:
            self.parts.append(data)

    raw = (transcript_html or "").strip()
    if not raw:
        return ""
    extractor = _Extractor()
    try:
        extractor.feed(raw)
        extractor.close()
        text = "".join(extractor.parts)
    except Exception:
        # Fallback se o HTML for inválido demais para o parser
        text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
        text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
        text = re.sub(r"(?i)<br\s*/?>", "\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html_lib.unescape(text)

    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _prepare_transcript(transcript_html: str, max_chars: int) -> str:
    plain = _html_to_plain_text(transcript_html)
    if not plain:
        return ""
    if len(plain) <= max_chars:
        return plain
    logger.warning(
        "kimi_ata_transcript_capped original_chars=%s max_chars=%s",
        len(plain),
        max_chars,
    )
    return (
        plain[:max_chars]
        + "\n\n[Transcrição truncada para geração por IA — revise o final no editor.]"
    )


class KimiLlmGateway:
    """Cliente OpenAI-compatible focado em gerar as 5 seções HTML da ata."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
        max_transcript_chars: int | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.KIMI_API_KEY) or ""
        self.base_url = (
            (base_url if base_url is not None else settings.KIMI_BASE_URL)
            or "https://openrouter.ai/api/v1"
        ).rstrip("/")
        self.model = (model if model is not None else settings.KIMI_MODEL) or "moonshotai/kimi-k3"
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else int(getattr(settings, "KIMI_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS) or DEFAULT_TIMEOUT_SECONDS)
        )
        self.max_transcript_chars = (
            max_transcript_chars
            if max_transcript_chars is not None
            else int(
                getattr(settings, "KIMI_MAX_TRANSCRIPT_CHARS", DEFAULT_MAX_TRANSCRIPT_CHARS)
                or DEFAULT_MAX_TRANSCRIPT_CHARS
            )
        )
        self.max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else int(
                getattr(settings, "KIMI_MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS)
                or DEFAULT_MAX_OUTPUT_TOKENS
            )
        )

    def generate_from_transcript(self, transcript_html: str) -> dict[str, str]:
        """Gera as 5 seções HTML a partir da transcrição (texto ou HTML)."""
        transcript = _prepare_transcript(transcript_html, self.max_transcript_chars)
        if not transcript:
            raise AtaGenerationError("Transcrição vazia: informe transcriptHtml.")
        if not self.api_key.strip():
            raise AtaGenerationError(
                "KIMI_API_KEY não configurada. Defina a variável de ambiente antes de gerar atas."
            )

        logger.info(
            "kimi_ata_generate_start model=%s transcript_chars=%s max_tokens=%s",
            self.model,
            len(transcript),
            self.max_output_tokens,
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Gere a ata em JSON a partir da transcrição em texto abaixo.\n\n"
                        f"{transcript}"
                    ),
                },
            ],
            "temperature": 0.2,
            "stream": False,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }

        url = f"{self.base_url}/chat/completions"
        try:
            # (connect, read) — connect rápido; read mais longo para modelos lentos
            response = requests.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=(15, self.timeout_seconds),
            )
        except requests.RequestException as exc:
            if _is_timeout_error(exc):
                logger.exception("kimi_ata_timeout")
                raise AtaGenerationError(
                    "Timeout ao chamar o provedor Kimi para gerar a ata. "
                    "Tente com uma transcrição menor ou aguarde e tente novamente."
                ) from exc
            logger.exception("kimi_ata_request_failed")
            raise AtaGenerationError(
                "Falha de rede ao chamar o provedor Kimi para gerar a ata."
            ) from exc

        if response.status_code != 200:
            logger.error(
                "kimi_ata_http_error status=%s body=%s",
                response.status_code,
                (response.text or "")[:500],
            )
            raise AtaGenerationError(
                f"Provedor Kimi retornou HTTP {response.status_code} ao gerar a ata."
            )

        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("kimi_ata_invalid_envelope")
            raise AtaGenerationError(
                "Resposta do provedor Kimi não é JSON válido."
            ) from exc

        choices = data.get("choices") or []
        if not choices:
            raise AtaGenerationError("Resposta do provedor Kimi sem choices.")

        content = str((choices[0].get("message") or {}).get("content") or "").strip()
        if not content:
            raise AtaGenerationError("Resposta do modelo Kimi sem conteúdo.")

        content = _strip_markdown_fences(content)
        try:
            sections = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.exception("kimi_ata_invalid_model_json")
            raise AtaGenerationError(
                "JSON das seções da ata retornado pelo modelo está malformado."
            ) from exc

        if not isinstance(sections, dict):
            raise AtaGenerationError(
                "JSON das seções da ata deve ser um objeto com as 5 chaves HTML."
            )

        missing = [key for key in REQUIRED_SECTION_KEYS if key not in sections]
        if missing:
            raise AtaGenerationError(
                "JSON incompleto da ata — faltam chaves: " + ", ".join(missing)
            )

        result: dict[str, str] = {}
        for key in REQUIRED_SECTION_KEYS:
            value = sections[key]
            result[key] = value if isinstance(value, str) else str(value)
        return result

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
