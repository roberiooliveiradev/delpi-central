"""Unified non-secret Pydantic AI runtime configuration (doc 243).

ONE checked-in JSON artifact is the single declarative source for every
non-secret, non-security-invariant tunable of the Pydantic AI
intelligence runtime: model identity, generation caps, agent limits,
context policy, budgets, tool-result projection and observability
switches — each in a typed profile selected at boot.

Fail-closed like the sibling governed-resource loaders: missing file,
malformed JSON, unknown keys or version, out-of-range values,
incompatible budgets, secret-shaped fields, missing/unknown profile or
an unknown ``DELIA_RUNTIME_PROFILE`` selector all raise
``PydanticAiRuntimeConfigError`` — never a silent default and never a
legacy fallback. Credentials, API keys and provider endpoints stay in
environment/secret bindings; this file carries tuning only.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from app.application.capability_provision.semantic_capability_support import (
    MAX_GOVERNED_ATTEMPTS,
)
from app.application.model_invocation.governed_retries import (
    LLM_CALL_MAX_ATTEMPTS,
)

_RESOURCE_ID = "delia.pydantic_ai.runtime"
_RESOURCE_KIND = "pydantic_ai_runtime"
_SCHEMA_VERSION = 1
_TOP_KEYS = frozenset(
    {
        "resource_id",
        "kind",
        "schema_version",
        "owner",
        "default_profile",
        "profiles",
    }
)
_SECTION_KEYS: Mapping[str, frozenset[str]] = {
    "model": frozenset({"provider", "model_name"}),
    "generation": frozenset({"max_output_tokens"}),
    "agent": frozenset(
        {
            "request_limit",
            "tool_calls_limit",
            "retries",
            "llm_call_max_attempts",
        }
    ),
    "context": frozenset(
        {
            "effective_context_window_tokens",
            "prior_turns_limit",
        }
    ),
    "budgets": frozenset(
        {
            "provider_call_timeout_seconds",
            "model_stage_timeout_seconds",
            "interaction_call_timeout_seconds",
            "turn_budget_seconds",
            "interaction_total_budget_seconds",
            "max_governed_attempts",
        }
    ),
    "tool_results": frozenset({"max_projection_chars"}),
    "observability": frozenset(
        {
            "record_model_id",
            "record_usage",
            "record_config_fingerprint",
        }
    ),
}
_MAX_PROFILES = 8
_PROFILE_NAME_RE = re.compile(r"^[a-z0-9_]{1,40}$")
_MODEL_NAME_MAX_CHARS = 128
# Secret/transport material must never live in this artifact: it is
# bound through environment/secret stores. Field names are checked
# case-insensitively at any depth inside a profile.
_FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "api_key",
        "apikey",
        "key",
        "secret",
        "client_secret",
        "password",
        "passphrase",
        "authorization",
        "bearer",
        "credential",
        "credentials",
        "base_url",
        "endpoint",
        "url",
        "token",
        "access_token",
    }
)

_SUPPORTED_PROVIDERS = frozenset({"openai_compatible"})

# Approved ceilings: profile values may lower, never raise, the
# governed invariants (docs 88/90 CP4 and doc 103 GATE 1).
_INT_RANGES: Mapping[str, tuple[int, int]] = {
    "max_output_tokens": (1, 65536),
    "request_limit": (1, 64),
    "tool_calls_limit": (1, 64),
    "retries": (0, 3),
    "llm_call_max_attempts": (1, LLM_CALL_MAX_ATTEMPTS),
    "effective_context_window_tokens": (256, 2_000_000),
    "prior_turns_limit": (0, 16),
    "max_governed_attempts": (1, MAX_GOVERNED_ATTEMPTS),
    "max_projection_chars": (500, 20_000),
}
_SECONDS_RANGES: Mapping[str, tuple[float, float]] = {
    "provider_call_timeout_seconds": (1.0, 300.0),
    "model_stage_timeout_seconds": (1.0, 300.0),
    "interaction_call_timeout_seconds": (1.0, 300.0),
    "turn_budget_seconds": (5.0, 900.0),
    "interaction_total_budget_seconds": (5.0, 900.0),
}


class PydanticAiRuntimeConfigError(Exception):
    """The unified runtime configuration is absent or invalid."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model_name: str


@dataclass(frozen=True)
class GenerationConfig:
    """Provider-side generation cap — ``None`` = unconfigured, never
    'unlimited' nor a claim about real provider capacity."""

    max_output_tokens: int | None


@dataclass(frozen=True)
class AgentConfig:
    request_limit: int
    tool_calls_limit: int
    retries: int
    llm_call_max_attempts: int


@dataclass(frozen=True)
class ContextConfig:
    """Effective input window honored by the deployment (``None`` =
    unknown → no pre-call budget enforcement) plus the bounded
    prior-turn context policy."""

    effective_context_window_tokens: int | None
    prior_turns_limit: int


@dataclass(frozen=True)
class BudgetsConfig:
    provider_call_timeout_seconds: float
    model_stage_timeout_seconds: float
    interaction_call_timeout_seconds: float
    turn_budget_seconds: float
    interaction_total_budget_seconds: float
    max_governed_attempts: int


@dataclass(frozen=True)
class ToolResultsConfig:
    max_projection_chars: int


@dataclass(frozen=True)
class ObservabilityConfig:
    record_model_id: bool
    record_usage: bool
    record_config_fingerprint: bool


@dataclass(frozen=True)
class RuntimeProfile:
    """One immutable effective configuration snapshot."""

    model: ModelConfig
    generation: GenerationConfig
    agent: AgentConfig
    context: ContextConfig
    budgets: BudgetsConfig
    tool_results: ToolResultsConfig
    observability: ObservabilityConfig


@dataclass(frozen=True)
class PydanticAiRuntimeConfig:
    """Validated document plus the resolved profile selection."""

    resource_id: str
    schema_version: int
    default_profile: str
    profile_name: str
    profile: RuntimeProfile
    fingerprint: str


def _fail(code: str, detail: str = "") -> None:
    raise PydanticAiRuntimeConfigError(code, detail)


def _check_no_secret_fields(value: object, *, trail: str = "") -> None:
    """Reject secret/transport-shaped field names at any depth."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key)
            if name.strip().lower() in _FORBIDDEN_FIELD_NAMES:
                _fail(
                    "runtime_config_forbidden_field",
                    f"field {trail + '.' + name!r} is not allowed in the "
                    "runtime config — secrets/endpoints bind via "
                    "environment",
                )
            _check_no_secret_fields(item, trail=f"{trail}.{name}")
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_no_secret_fields(item, trail=trail)


def _section(
    profile: Mapping, name: str, *, profile_name: str
) -> Mapping:
    value = profile.get(name)
    if not isinstance(value, Mapping):
        _fail(
            "runtime_config_invalid",
            f"profile {profile_name!r} section {name!r} missing or "
            "not an object",
        )
    extra = set(value) - _SECTION_KEYS[name]
    if extra:
        _fail(
            "runtime_config_invalid",
            f"profile {profile_name!r} section {name!r} unsupported "
            f"fields: {sorted(extra)}",
        )
    missing = _SECTION_KEYS[name] - set(value)
    if missing:
        _fail(
            "runtime_config_invalid",
            f"profile {profile_name!r} section {name!r} missing "
            f"fields: {sorted(missing)}",
        )
    return value


def _int_field(
    section: Mapping, name: str, *, profile_name: str, section_name: str
) -> int:
    value = section[name]
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(
            "runtime_config_invalid",
            f"{profile_name}.{section_name}.{name} must be an integer",
        )
    low, high = _INT_RANGES[name]
    if not low <= value <= high:
        _fail(
            "runtime_config_invalid",
            f"{profile_name}.{section_name}.{name}={value} outside "
            f"[{low}, {high}]",
        )
    return value


def _optional_int_field(
    section: Mapping, name: str, *, profile_name: str, section_name: str
) -> int | None:
    value = section[name]
    if value is None:
        return None
    return _int_field(
        section, name, profile_name=profile_name, section_name=section_name
    )


def _seconds_field(
    section: Mapping, name: str, *, profile_name: str, section_name: str
) -> float:
    value = section[name]
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        _fail(
            "runtime_config_invalid",
            f"{profile_name}.{section_name}.{name} must be a number",
        )
    low, high = _SECONDS_RANGES[name]
    number = float(value)
    if not low <= number <= high:
        _fail(
            "runtime_config_invalid",
            f"{profile_name}.{section_name}.{name}={number} outside "
            f"[{low}, {high}]",
        )
    return number


def _bool_field(
    section: Mapping, name: str, *, profile_name: str, section_name: str
) -> bool:
    value = section[name]
    if not isinstance(value, bool):
        _fail(
            "runtime_config_invalid",
            f"{profile_name}.{section_name}.{name} must be a boolean",
        )
    return value


def _profile(
    data: Mapping, *, profile_name: str
) -> RuntimeProfile:
    _check_no_secret_fields(data, trail=profile_name)
    model = _section(data, "model", profile_name=profile_name)
    provider = model["provider"]
    if not isinstance(provider, str) or provider not in (
        _SUPPORTED_PROVIDERS
    ):
        _fail(
            "runtime_config_invalid",
            f"{profile_name}.model.provider={provider!r} — supported: "
            f"{sorted(_SUPPORTED_PROVIDERS)}",
        )
    model_name = model["model_name"]
    if (
        not isinstance(model_name, str)
        or not model_name.strip()
        or len(model_name) > _MODEL_NAME_MAX_CHARS
    ):
        _fail(
            "runtime_config_invalid",
            f"{profile_name}.model.model_name missing or oversized",
        )
    generation = _section(
        data, "generation", profile_name=profile_name
    )
    agent = _section(data, "agent", profile_name=profile_name)
    context = _section(data, "context", profile_name=profile_name)
    budgets = _section(data, "budgets", profile_name=profile_name)
    tool_results = _section(
        data, "tool_results", profile_name=profile_name
    )
    observability = _section(
        data, "observability", profile_name=profile_name
    )
    parsed_budgets = BudgetsConfig(
        provider_call_timeout_seconds=_seconds_field(
            budgets,
            "provider_call_timeout_seconds",
            profile_name=profile_name,
            section_name="budgets",
        ),
        model_stage_timeout_seconds=_seconds_field(
            budgets,
            "model_stage_timeout_seconds",
            profile_name=profile_name,
            section_name="budgets",
        ),
        interaction_call_timeout_seconds=_seconds_field(
            budgets,
            "interaction_call_timeout_seconds",
            profile_name=profile_name,
            section_name="budgets",
        ),
        turn_budget_seconds=_seconds_field(
            budgets,
            "turn_budget_seconds",
            profile_name=profile_name,
            section_name="budgets",
        ),
        interaction_total_budget_seconds=_seconds_field(
            budgets,
            "interaction_total_budget_seconds",
            profile_name=profile_name,
            section_name="budgets",
        ),
        max_governed_attempts=_int_field(
            budgets,
            "max_governed_attempts",
            profile_name=profile_name,
            section_name="budgets",
        ),
    )
    # Cross-field constraints (doc 243 §3): a per-call/stage ceiling
    # may never outlive the turn deadline, and the monotonic
    # interaction cap must cover at least one whole turn.
    if (
        parsed_budgets.turn_budget_seconds
        > parsed_budgets.interaction_total_budget_seconds
    ):
        _fail(
            "runtime_config_invalid",
            f"{profile_name}.budgets.turn_budget_seconds exceeds "
            "interaction_total_budget_seconds",
        )
    for call_key in (
        "provider_call_timeout_seconds",
        "model_stage_timeout_seconds",
        "interaction_call_timeout_seconds",
    ):
        if (
            getattr(parsed_budgets, call_key)
            > parsed_budgets.turn_budget_seconds
        ):
            _fail(
                "runtime_config_invalid",
                f"{profile_name}.budgets.{call_key} exceeds "
                "turn_budget_seconds",
            )
    return RuntimeProfile(
        model=ModelConfig(
            provider=provider,
            model_name=model_name.strip(),
        ),
        generation=GenerationConfig(
            max_output_tokens=_optional_int_field(
                generation,
                "max_output_tokens",
                profile_name=profile_name,
                section_name="generation",
            ),
        ),
        agent=AgentConfig(
            request_limit=_int_field(
                agent,
                "request_limit",
                profile_name=profile_name,
                section_name="agent",
            ),
            tool_calls_limit=_int_field(
                agent,
                "tool_calls_limit",
                profile_name=profile_name,
                section_name="agent",
            ),
            retries=_int_field(
                agent,
                "retries",
                profile_name=profile_name,
                section_name="agent",
            ),
            llm_call_max_attempts=_int_field(
                agent,
                "llm_call_max_attempts",
                profile_name=profile_name,
                section_name="agent",
            ),
        ),
        context=ContextConfig(
            effective_context_window_tokens=_optional_int_field(
                context,
                "effective_context_window_tokens",
                profile_name=profile_name,
                section_name="context",
            ),
            prior_turns_limit=_int_field(
                context,
                "prior_turns_limit",
                profile_name=profile_name,
                section_name="context",
            ),
        ),
        budgets=parsed_budgets,
        tool_results=ToolResultsConfig(
            max_projection_chars=_int_field(
                tool_results,
                "max_projection_chars",
                profile_name=profile_name,
                section_name="tool_results",
            ),
        ),
        observability=ObservabilityConfig(
            record_model_id=_bool_field(
                observability,
                "record_model_id",
                profile_name=profile_name,
                section_name="observability",
            ),
            record_usage=_bool_field(
                observability,
                "record_usage",
                profile_name=profile_name,
                section_name="observability",
            ),
            record_config_fingerprint=_bool_field(
                observability,
                "record_config_fingerprint",
                profile_name=profile_name,
                section_name="observability",
            ),
        ),
    )


def load_pydantic_ai_runtime_config(
    path: str | Path,
    *,
    profile_selector: str | None = None,
) -> PydanticAiRuntimeConfig:
    """Load, validate and resolve ONE runtime profile — whole or none.

    ``profile_selector`` is an explicit deployment-selected profile
    identifier (``DELIA_RUNTIME_PROFILE``); absent it resolves to the
    document's ``default_profile``. An unknown selector fails closed.
    The fingerprint is a non-secret digest of the effective profile,
    logged at boot/eval for configuration lineage.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        _fail("runtime_config_unreadable", str(exc))
    try:
        data = json.loads(raw)
    except ValueError:
        _fail("runtime_config_invalid", "not valid JSON")
    if not isinstance(data, Mapping):
        _fail("runtime_config_invalid", "document is not an object")
    extra = set(data) - _TOP_KEYS
    if extra:
        _fail(
            "runtime_config_invalid",
            f"unsupported fields: {sorted(extra)}",
        )
    missing = _TOP_KEYS - set(data)
    if missing:
        _fail(
            "runtime_config_invalid",
            f"missing fields: {sorted(missing)}",
        )
    if data.get("resource_id") != _RESOURCE_ID:
        _fail(
            "runtime_config_invalid",
            f"unexpected resource_id: {data.get('resource_id')!r}",
        )
    if data.get("kind") != _RESOURCE_KIND:
        _fail(
            "runtime_config_invalid",
            f"unexpected kind: {data.get('kind')!r}",
        )
    if data.get("schema_version") != _SCHEMA_VERSION:
        _fail(
            "runtime_config_invalid",
            f"unsupported schema_version: "
            f"{data.get('schema_version')!r}",
        )
    if not isinstance(data.get("owner"), str) or not data["owner"].strip():
        _fail("runtime_config_invalid", "owner missing")
    default_profile = data.get("default_profile")
    profiles = data.get("profiles")
    if not isinstance(profiles, Mapping) or not profiles:
        _fail(
            "runtime_config_invalid",
            "profiles missing or empty",
        )
    if len(profiles) > _MAX_PROFILES:
        _fail("runtime_config_invalid", "profiles oversized")
    for name in profiles:
        if not isinstance(name, str) or not _PROFILE_NAME_RE.match(name):
            _fail(
                "runtime_config_invalid",
                f"invalid profile name: {name!r}",
            )
        if not isinstance(profiles[name], Mapping):
            _fail(
                "runtime_config_invalid",
                f"profile {name!r} is not an object",
            )
    if (
        not isinstance(default_profile, str)
        or default_profile not in profiles
    ):
        _fail(
            "runtime_config_invalid",
            f"default_profile {default_profile!r} is not a declared "
            "profile",
        )
    selector = (
        profile_selector.strip()
        if isinstance(profile_selector, str) and profile_selector.strip()
        else default_profile
    )
    if selector not in profiles:
        _fail(
            "runtime_config_invalid",
            f"unknown profile selector: {profile_selector!r}",
        )
    profile_data = profiles[selector]
    extra = set(profile_data) - set(_SECTION_KEYS)
    if extra:
        _fail(
            "runtime_config_invalid",
            f"profile {selector!r} unsupported sections: "
            f"{sorted(extra)}",
        )
    profile = _profile(profile_data, profile_name=selector)
    canonical = json.dumps(
        {selector: profile_data}, sort_keys=True, ensure_ascii=False
    )
    return PydanticAiRuntimeConfig(
        resource_id=_RESOURCE_ID,
        schema_version=_SCHEMA_VERSION,
        default_profile=default_profile,
        profile_name=selector,
        profile=profile,
        fingerprint=hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()[:16],
    )
