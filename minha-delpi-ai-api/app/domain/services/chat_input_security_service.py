import re
import unicodedata
from dataclasses import dataclass

from app.domain.services.chat_domain_config_service import ChatDomainConfigService


@dataclass(frozen=True)
class ChatInputSecurityResult:
    sanitized: str
    original_length: int
    sanitized_length: int
    risk_score: float
    risk_level: str
    flags: tuple[str, ...]
    blocked: bool
    flagged: bool
    block_reason: str | None


class ChatInputSecurityService:
    CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    EXCESSIVE_NEWLINES_PATTERN = re.compile(r"\n{4,}")

    INJECTION_RULES: tuple[tuple[str, float, str], ...] = (
        (
            r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|prompts)",
            0.55,
            "prompt_injection.ignore_instructions",
        ),
        (
            r"(?i)disregard\s+(all\s+)?(your\s+)?(instructions|rules|system\s+prompt)",
            0.5,
            "prompt_injection.disregard_instructions",
        ),
        (
            r"(?i)forget\s+(everything|all)\s+(you\s+)?(were|have\s+been)\s+told",
            0.45,
            "prompt_injection.forget_instructions",
        ),
        (
            r"(?i)you\s+are\s+now\s+(a|an|in)\s+",
            0.4,
            "prompt_injection.role_override",
        ),
        (
            r"(?i)act\s+as\s+(if\s+)?(you\s+)?(have\s+)?no\s+(rules|restrictions|limits)",
            0.5,
            "prompt_injection.no_restrictions",
        ),
        (
            r"(?i)\bDAN\s+mode\b",
            0.55,
            "prompt_injection.dan_mode",
        ),
        (
            r"(?i)\bjailbreak\b",
            0.55,
            "prompt_injection.jailbreak",
        ),
        (
            r"(?i)reveal\s+(your\s+)?(system\s+)?prompt",
            0.45,
            "prompt_injection.reveal_prompt",
        ),
        (
            r"(?i)override\s+(safety|security|content)\s+(policy|rules|filters)",
            0.5,
            "prompt_injection.override_safety",
        ),
        (
            r"(?i)\bsystem\s*:\s*",
            0.35,
            "prompt_injection.system_role_marker",
        ),
        (
            r"(?i)\[INST\]|\[/INST\]",
            0.4,
            "prompt_injection.inst_markers",
        ),
        (
            r"(?i)new\s+instructions\s*:",
            0.35,
            "prompt_injection.new_instructions",
        ),
        (
            r"(?i)pretend\s+you\s+are\s+(not\s+)?(bound|restricted|limited)",
            0.35,
            "prompt_injection.pretend_unrestricted",
        ),
        (
            r"(?i)developer\s+mode\s+(enabled|on)",
            0.35,
            "prompt_injection.developer_mode",
        ),
        (
            r"(?i)do\s+anything\s+now",
            0.3,
            "prompt_injection.do_anything_now",
        ),
    )

    def analyze(self, value: str | None) -> ChatInputSecurityResult:
        original = str(value or "")
        sanitized = self._sanitize(original)
        flags: list[str] = []
        risk_score = 0.0

        if not sanitized.strip():
            return ChatInputSecurityResult(
                sanitized=sanitized,
                original_length=len(original),
                sanitized_length=len(sanitized),
                risk_score=0.0,
                risk_level="low",
                flags=(),
                blocked=False,
                flagged=False,
                block_reason=None,
            )

        if self.CONTROL_CHAR_PATTERN.search(original):
            flags.append("sanitization.control_chars_removed")
            risk_score += 0.15

        if len(original) > ChatDomainConfigService.chat_message_max_chars():
            flags.append("limits.message_too_long")
            risk_score += 0.25

        for pattern, weight, flag in self.INJECTION_RULES:
            if re.search(pattern, sanitized):
                flags.append(flag)
                risk_score += weight

        risk_score = min(round(risk_score, 3), 1.0)
        risk_level = self._risk_level(risk_score)
        blocked = self._should_block(risk_score=risk_score, sanitized=sanitized)
        flagged = (
            not blocked
            and risk_score >= ChatDomainConfigService.chat_input_security_flag_threshold()
        )

        block_reason = None

        if blocked:
            block_reason = (
                "A mensagem foi bloqueada por indicadores de prompt injection "
                "ou violação de limites operacionais."
            )

        return ChatInputSecurityResult(
            sanitized=sanitized,
            original_length=len(original),
            sanitized_length=len(sanitized),
            risk_score=risk_score,
            risk_level=risk_level,
            flags=tuple(dict.fromkeys(flags)),
            blocked=blocked,
            flagged=flagged,
            block_reason=block_reason,
        )

    def build_config(self) -> dict:
        return {
            "enabled": ChatDomainConfigService.chat_input_security_enabled(),
            "mode": ChatDomainConfigService.chat_input_security_mode(),
            "messageMaxChars": ChatDomainConfigService.chat_message_max_chars(),
            "blockThreshold": ChatDomainConfigService.chat_input_security_block_threshold(),
            "flagThreshold": ChatDomainConfigService.chat_input_security_flag_threshold(),
            "rateLimitEnabled": ChatDomainConfigService.rate_limit_enabled(),
            "rateLimits": {
                "chatMessagesPerWindow": ChatDomainConfigService.rate_limit_chat_messages_per_window(),
                "toolCallsPerWindow": ChatDomainConfigService.rate_limit_tool_calls_per_window(),
                "knowledgeWritesPerWindow": ChatDomainConfigService.rate_limit_knowledge_writes_per_window(),
                "adminActionsPerWindow": ChatDomainConfigService.rate_limit_admin_actions_per_window(),
                "windowSeconds": ChatDomainConfigService.rate_limit_window_seconds(),
            },
            "injectionRuleCount": len(self.INJECTION_RULES),
        }

    def _sanitize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value)
        without_controls = self.CONTROL_CHAR_PATTERN.sub("", normalized)
        collapsed_newlines = self.EXCESSIVE_NEWLINES_PATTERN.sub("\n\n\n", without_controls)
        stripped = collapsed_newlines.strip()

        if len(stripped) > ChatDomainConfigService.chat_message_max_chars():
            stripped = stripped[: ChatDomainConfigService.chat_message_max_chars()]

        return stripped

    def _risk_level(self, risk_score: float) -> str:
        if risk_score >= ChatDomainConfigService.chat_input_security_block_threshold():
            return "critical"
        if risk_score >= ChatDomainConfigService.chat_input_security_flag_threshold():
            return "high"
        if risk_score >= 0.2:
            return "medium"
        return "low"

    def _should_block(self, *, risk_score: float, sanitized: str) -> bool:
        if not ChatDomainConfigService.chat_input_security_enabled():
            return False

        if not sanitized.strip():
            return True

        if risk_score < ChatDomainConfigService.chat_input_security_block_threshold():
            return False

        if ChatDomainConfigService.chat_input_security_mode() == "monitor":
            return False

        return True
