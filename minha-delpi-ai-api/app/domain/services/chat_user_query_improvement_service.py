"""Melhoria gated da pergunta do usuário (typos) antes de intent/tools."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar

from app.domain.entities.llm_generation_config import LlmGenerationConfig
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_user_query_improvement_content_service import (
    ChatUserQueryImprovementContentService,
)

_CONTENT = ChatUserQueryImprovementContentService
_PRODUCT_CODE_RE = re.compile(r"\b\d{5,}\b")


@dataclass(frozen=True)
class UserQueryImprovementResult:
    original: str
    improved: str
    applied: bool
    reason: str
    changes: tuple[dict[str, str], ...] = ()
    source: str = "none"

    @property
    def message_for_intelligence(self) -> str:
        if self.applied and str(self.improved or "").strip():
            return str(self.improved).strip()
        return str(self.original or "").strip()

    def as_metadata(self) -> dict[str, Any]:
        return {
            "original": self.original,
            "improved": self.improved,
            "applied": self.applied,
            "reason": self.reason,
            "source": self.source,
            "changes": list(self.changes),
            "messageForIntelligence": self.message_for_intelligence,
        }


class ChatUserQueryImprovementService:
    _gateway: ClassVar[LlmGatewayPort | None] = None

    @classmethod
    def configure(cls, gateway: LlmGatewayPort | None) -> None:
        cls._gateway = gateway

    @classmethod
    def improve(
        cls,
        message: str,
        *,
        response_mode: str | None = None,
        product_code_hint: str | None = None,
        llm_gateway: LlmGatewayPort | None = None,
    ) -> UserQueryImprovementResult:
        original = str(message or "")
        if not _CONTENT.enabled():
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("disabled"),
            )

        stripped = original.strip()
        if not stripped:
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("empty"),
            )

        if cls._matches_skip(stripped):
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("skipMarker"),
            )

        max_input = _CONTENT.limit_int("maxInputChars", 500)
        work = stripped if len(stripped) <= max_input else stripped[:max_input]

        rules_text = ChatMessageNormalizationService.apply_typo_rules(work)
        # Canonicalização só de acentos (descrição→descricao) não conta como rewrite.
        if ChatMessageNormalizationService.strip_accents(
            rules_text
        ) == ChatMessageNormalizationService.strip_accents(work):
            rules_text = work
        rules_changed = rules_text.strip() != work.strip()

        if rules_changed and not cls._gate_needs_llm(
            rules_text,
            product_code_hint=product_code_hint,
        ):
            changes = cls._diff_tokens(work, rules_text)
            return cls._result(
                original,
                rules_text if len(stripped) <= max_input else rules_text + stripped[max_input:],
                applied=True,
                reason=_CONTENT.reason("rulesOnly"),
                changes=changes,
                source="rules",
            )

        if not cls._gate_needs_llm(rules_text, product_code_hint=product_code_hint):
            if rules_changed:
                changes = cls._diff_tokens(work, rules_text)
                return cls._result(
                    original,
                    rules_text,
                    applied=True,
                    reason=_CONTENT.reason("rulesOnly"),
                    changes=changes,
                    source="rules",
                )
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("alreadyClean"),
            )

        gateway = llm_gateway or cls._gateway
        if gateway is None:
            if rules_changed:
                return cls._result(
                    original,
                    rules_text,
                    applied=True,
                    reason=_CONTENT.reason("rulesOnly"),
                    changes=cls._diff_tokens(work, rules_text),
                    source="rules",
                )
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("gateClosed"),
            )

        llm_text = cls._call_llm(
            rules_text if rules_changed else work,
            response_mode=response_mode,
            gateway=gateway,
        )
        if not llm_text:
            if rules_changed:
                return cls._result(
                    original,
                    rules_text,
                    applied=True,
                    reason=_CONTENT.reason("rulesOnly"),
                    changes=cls._diff_tokens(work, rules_text),
                    source="rules",
                )
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("llmError"),
            )

        candidate = cls._sanitize_llm_output(llm_text, fallback=rules_text if rules_changed else work)
        if not candidate:
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("llmRejectedEmpty"),
            )

        base_for_codes = work
        if not cls._preserves_product_codes(base_for_codes, candidate):
            if rules_changed:
                return cls._result(
                    original,
                    rules_text,
                    applied=True,
                    reason=_CONTENT.reason("rulesOnly"),
                    changes=cls._diff_tokens(work, rules_text),
                    source="rules",
                )
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("llmRejectedCodeDrop"),
            )

        if candidate.strip() == work.strip():
            if rules_changed and rules_text.strip() != work.strip():
                return cls._result(
                    original,
                    rules_text,
                    applied=True,
                    reason=_CONTENT.reason("rulesOnly"),
                    changes=cls._diff_tokens(work, rules_text),
                    source="rules",
                )
            return cls._result(
                original,
                original,
                applied=False,
                reason=_CONTENT.reason("llmNoop"),
            )

        return cls._result(
            original,
            candidate,
            applied=True,
            reason=_CONTENT.reason("llmApplied"),
            changes=cls._diff_tokens(work, candidate),
            source="llm",
        )

    @classmethod
    def _result(
        cls,
        original: str,
        improved: str,
        *,
        applied: bool,
        reason: str,
        changes: tuple[dict[str, str], ...] = (),
        source: str = "none",
    ) -> UserQueryImprovementResult:
        return UserQueryImprovementResult(
            original=original,
            improved=improved,
            applied=applied,
            reason=reason,
            changes=changes,
            source=source,
        )

    @classmethod
    def _matches_skip(cls, message: str) -> bool:
        for key in ("corrijaPrefix", "sqlFence", "selectLead"):
            pattern = _CONTENT.compile_skip_pattern(key)
            if pattern and pattern.search(message):
                return True
        return False

    @classmethod
    def _gate_needs_llm(
        cls,
        message: str,
        *,
        product_code_hint: str | None = None,
    ) -> bool:
        # Stems quebrados no texto pós-regras A (sem fuzzy): fuzzy de matching
        # pode “corrigir” só para classify e deixar a mensagem de intel com typo.
        accent_folded = ChatMessageNormalizationService.strip_accents(
            str(message or "")
        ).lower()
        if not accent_folded.strip():
            return False

        for stem in _CONTENT.broken_operational_stems():
            if stem and stem in accent_folded:
                return True

        codes = _PRODUCT_CODE_RE.findall(message)
        hint = str(product_code_hint or "").strip()
        if hint and hint not in codes:
            codes.append(hint)

        min_digits = _CONTENT.product_code_min_digits()
        has_code = any(len(code) >= min_digits for code in codes)
        if not has_code:
            return False

        # Código presente + possível verbo de cadastro “quebrado” residual
        # (ex.: stem descri* sem descricao completo após regras).
        has_cadastro_stem = any(
            stem and stem in accent_folded for stem in _CONTENT.cadastro_verb_stems()
        )
        if not has_cadastro_stem:
            return False

        if (
            "descricao" in accent_folded
            or "estrutura" in accent_folded
            or "estoque" in accent_folded
        ):
            return False

        # Verbo/stem de cadastro sem forma canônica → ainda precisa LLM
        return any(
            stem in accent_folded and stem not in {"produto", "cadastro", "cadastr"}
            for stem in _CONTENT.cadastro_verb_stems()
        )

    @classmethod
    def _call_llm(
        cls,
        message: str,
        *,
        response_mode: str | None,
        gateway: LlmGatewayPort,
    ) -> str:
        from app.domain.services.chat_llm_generation_context_service import (
            llm_generation_scope,
        )
        from app.domain.services.chat_response_mode_service import ChatResponseModeService

        mode = ChatResponseModeService.normalize(response_mode) or "fast"
        base = ChatResponseModeService.resolve(mode)
        max_tokens = _CONTENT.limit_int("maxTokens", 128)
        temperature = _CONTENT.limit_float("temperature", 0.0)
        config = LlmGenerationConfig(
            model=base.model,
            max_tokens=max_tokens,
            num_ctx=min(int(base.num_ctx or 4096), 4096),
            temperature=temperature,
            response_mode=mode,
        )
        messages = [
            {"role": "system", "content": _CONTENT.system_prompt()},
            {
                "role": "user",
                "content": _CONTENT.format_user_prompt(message=message),
            },
        ]
        try:
            with llm_generation_scope(config):
                return str(gateway.generate(messages) or "").strip()
        except Exception:
            return ""

    @classmethod
    def _sanitize_llm_output(cls, text: str, *, fallback: str) -> str:
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""
        # Uma linha; remove aspas envolventes e prefixos comuns
        cleaned = cleaned.splitlines()[0].strip()
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1].strip()
        max_out = _CONTENT.limit_int("maxOutputChars", 600)
        if len(cleaned) > max_out:
            cleaned = cleaned[:max_out].strip()
        return cleaned or fallback

    @classmethod
    def _preserves_product_codes(cls, original: str, candidate: str) -> bool:
        original_codes = set(_PRODUCT_CODE_RE.findall(original))
        if not original_codes:
            return True
        candidate_codes = set(_PRODUCT_CODE_RE.findall(candidate))
        return original_codes.issubset(candidate_codes)

    @classmethod
    def _diff_tokens(
        cls, before: str, after: str
    ) -> tuple[dict[str, str], ...]:
        before_tokens = before.split()
        after_tokens = after.split()
        changes: list[dict[str, str]] = []
        for left, right in zip(before_tokens, after_tokens):
            if left != right:
                changes.append({"from": left, "to": right})
        if len(before_tokens) != len(after_tokens) and not changes:
            changes.append({"from": before[:80], "to": after[:80]})
        return tuple(changes[:8])
