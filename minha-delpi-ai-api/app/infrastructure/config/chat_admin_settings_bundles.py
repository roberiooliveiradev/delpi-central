from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal

from app.infrastructure.config.settings import Settings

FieldKind = Literal["bool", "float", "int"]


@dataclass(frozen=True)
class AdminSettingsFieldSpec:
    json_key: str
    kind: FieldKind
    default: Callable[[], Any]
    min_int: int = 1
    max_int: int = 100


@dataclass(frozen=True)
class AdminSettingsBundleSpec:
    storage_key: str
    fields: tuple[AdminSettingsFieldSpec, ...]


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _float(value: Any, default: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    if value is None:
        parsed = float(default)
    else:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = float(default)
    return max(min_value, min(parsed, max_value))


def _int(value: Any, default: int, *, min_value: int, max_value: int) -> int:
    if value is None:
        parsed = int(default)
    else:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = int(default)
    return max(min_value, min(parsed, max_value))


def build_defaults_payload(spec: AdminSettingsBundleSpec) -> dict[str, Any]:
    return {field.json_key: field.default() for field in spec.fields}


def resolve_bundle_payload(
    *,
    spec: AdminSettingsBundleSpec,
    stored: dict[str, Any] | None,
) -> dict[str, Any]:
    defaults = build_defaults_payload(spec)

    if not stored:
        return defaults

    resolved = dict(defaults)

    for field in spec.fields:
        if field.json_key not in stored:
            continue

        raw = stored.get(field.json_key)
        default = defaults[field.json_key]

        if field.kind == "bool":
            resolved[field.json_key] = _bool(raw, bool(default))
        elif field.kind == "float":
            resolved[field.json_key] = _float(raw, float(default))
        elif field.kind == "int":
            resolved[field.json_key] = _int(
                raw,
                int(default),
                min_value=field.min_int,
                max_value=field.max_int,
            )

    return resolved


CHAT_RESPONSE_MODE_BUNDLE = AdminSettingsBundleSpec(
    storage_key="chat_response_mode_settings",
    fields=(
        AdminSettingsFieldSpec(
            "responseModesEnabled",
            "bool",
            lambda: bool(Settings.CHAT_RESPONSE_MODES_ENABLED),
        ),
    ),
)

CHAT_VISION_BUNDLE = AdminSettingsBundleSpec(
    storage_key="chat_vision_settings",
    fields=(
        AdminSettingsFieldSpec(
            "documentVisionEnabled",
            "bool",
            lambda: bool(Settings.CHAT_DOCUMENT_VISION_ENABLED),
        ),
        AdminSettingsFieldSpec(
            "documentVisionAutoWithDrawing",
            "bool",
            lambda: bool(Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING),
        ),
        AdminSettingsFieldSpec(
            "documentVisionAutoVlmFallback",
            "bool",
            lambda: bool(Settings.CHAT_DOCUMENT_VISION_AUTO_VLM_FALLBACK),
        ),
        AdminSettingsFieldSpec(
            "attachmentImageOcrEnabled",
            "bool",
            lambda: bool(Settings.CHAT_ATTACHMENT_IMAGE_OCR_ENABLED),
        ),
        AdminSettingsFieldSpec(
            "documentVisionStampCropEnabled",
            "bool",
            lambda: bool(Settings.CHAT_DOCUMENT_VISION_STAMP_CROP_ENABLED),
        ),
        AdminSettingsFieldSpec(
            "documentVisionImageDescribeEnabled",
            "bool",
            lambda: bool(Settings.CHAT_DOCUMENT_VISION_IMAGE_DESCRIBE_ENABLED),
        ),
        AdminSettingsFieldSpec(
            "documentVisionMaxPages",
            "int",
            lambda: int(Settings.CHAT_DOCUMENT_VISION_MAX_PAGES),
            min_int=1,
            max_int=30,
        ),
        AdminSettingsFieldSpec(
            "documentVisionMaxChars",
            "int",
            lambda: int(Settings.CHAT_DOCUMENT_VISION_MAX_CHARS),
            min_int=1000,
            max_int=50000,
        ),
    ),
)

CHAT_LEARNING_PIPELINE_BUNDLE = AdminSettingsBundleSpec(
    storage_key="chat_learning_pipeline_settings",
    fields=(
        AdminSettingsFieldSpec(
            "learningEnabled",
            "bool",
            lambda: bool(Settings.CHAT_LEARNING_ENABLED),
        ),
        AdminSettingsFieldSpec(
            "typingCorrectionEnabled",
            "bool",
            lambda: bool(Settings.CHAT_TYPING_CORRECTION_ENABLED),
        ),
        AdminSettingsFieldSpec(
            "typingCorrectionFuzzyEnabled",
            "bool",
            lambda: bool(Settings.CHAT_TYPING_CORRECTION_FUZZY_ENABLED),
        ),
        AdminSettingsFieldSpec(
            "learningApplyVocabulary",
            "bool",
            lambda: bool(Settings.CHAT_LEARNING_APPLY_VOCABULARY),
        ),
        AdminSettingsFieldSpec(
            "learningCaptureFromFeedback",
            "bool",
            lambda: bool(Settings.CHAT_LEARNING_CAPTURE_FROM_FEEDBACK),
        ),
        AdminSettingsFieldSpec(
            "learningCaptureFromTurn",
            "bool",
            lambda: bool(Settings.CHAT_LEARNING_CAPTURE_FROM_TURN),
        ),
        AdminSettingsFieldSpec(
            "learningAutoApproveEnabled",
            "bool",
            lambda: bool(Settings.CHAT_LEARNING_AUTO_APPROVE_ENABLED),
        ),
        AdminSettingsFieldSpec(
            "learningAutoApproveMinConfidence",
            "float",
            lambda: float(Settings.CHAT_LEARNING_AUTO_APPROVE_MIN_CONFIDENCE),
        ),
        AdminSettingsFieldSpec(
            "learningGlossaryRetrieval",
            "bool",
            lambda: bool(Settings.CHAT_LEARNING_GLOSSARY_RETRIEVAL),
        ),
        AdminSettingsFieldSpec(
            "learningGlossaryCapture",
            "bool",
            lambda: bool(Settings.CHAT_LEARNING_GLOSSARY_CAPTURE),
        ),
        AdminSettingsFieldSpec(
            "learningTermConfirmationEnabled",
            "bool",
            lambda: bool(Settings.CHAT_LEARNING_TERM_CONFIRMATION_ENABLED),
        ),
    ),
)
