from __future__ import annotations

import re
from dataclasses import dataclass

from bpmn_modeler.application.validation import InputSafetyEvidence
from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)

MAX_INPUT_BYTES = 10_485_760
MAX_CANONICAL_UTF8_BYTES = 10_485_760
MAX_XML_DEPTH = 64
MAX_XML_ELEMENTS = 100_000
MAX_ATTRIBUTES_PER_ELEMENT = 128
MAX_TEXT_NODE_BYTES = 1_048_576

_BUILTIN_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}

_DECLARED_ENCODING_RE = re.compile(rb"<\?xml[^>]*encoding\s*=\s*[\"']([\w.-]+)[\"']")
_ENTITY_DECL_RE = re.compile(r"<!ENTITY\b")
_EXTERNAL_ENTITY_RE = re.compile(r"<!ENTITY\b[^>]*\b(?:SYSTEM|PUBLIC)\b", re.DOTALL)
_ENTITY_REF_RE = re.compile(r"&([A-Za-z_][\w.:-]*);")
_DOCTYPE_RE = re.compile(r"<!DOCTYPE\b")

_TAG_TOKEN_RE = re.compile(
    r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<!DOCTYPE[^>\[]*(?:\[.*?\])?\s*>|"
    r"<\?.*?\?>|</?[A-Za-z_][^>]*?/?>|<|>",
    re.DOTALL,
)
_START_TAG_NAME_RE = re.compile(r"^<([A-Za-z_][\w.:-]*)")
_END_TAG_RE = re.compile(r"^</")
_ATTR_ASSIGN_RE = re.compile(r"[\w:.-]+\s*=")


@dataclass(frozen=True, slots=True)
class IntakeResult:
    """Boundary output of the secure intake adapter."""

    evidence: InputSafetyEvidence
    artifact: CanonicalBpmnArtifact | None  # None when no usable XML text
    oversized: bool  # raw body exceeds MAX_INPUT_BYTES (transport 413)


def _detect_encoding(raw: bytes) -> str | None:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8"
    if raw.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if raw.startswith(b"\xfe\xff"):
        return "utf-16-be"
    return None


def _decode(raw: bytes) -> tuple[str | None, str | None, str | None, bool]:
    bom_encoding = _detect_encoding(raw)
    declared: str | None = None
    match = _DECLARED_ENCODING_RE.match(raw[:256])
    if match:
        declared = match.group(1).decode("ascii", errors="replace").lower()

    candidates: list[str] = []
    if bom_encoding:
        candidates.append("utf-8-sig" if bom_encoding == "utf-8" else bom_encoding)
    candidates.append("utf-8")
    if declared and declared not in candidates:
        candidates.append(declared)

    for encoding in candidates:
        try:
            return raw.decode(encoding), encoding, declared, True
        except (UnicodeDecodeError, LookupError):
            continue
    return None, None, declared, False


def _scan_structure(text: str) -> tuple[int, int, bool]:
    """Bounded scan of element depth / counts without building a tree.

    Returns (max_depth, element_count, text_node_oversize). Attribute count
    violations fold into element_count via a flag check in the caller.
    """
    depth = 0
    max_depth = 0
    elements = 0
    attr_violation = False
    text_oversize = False
    position = 0
    length = len(text)
    for match in _TAG_TOKEN_RE.finditer(text):
        token = match.group(0)
        between = text[position : match.start()]
        if len(between.encode("utf-8", errors="ignore")) > MAX_TEXT_NODE_BYTES:
            text_oversize = True
        position = match.end()
        if token.startswith("</"):
            depth = max(depth - 1, 0)
        elif token.startswith("<") and not token.startswith(
            ("<!", "<?", "<![CDATA[")
        ):
            if _START_TAG_NAME_RE.match(token):
                elements += 1
                if len(_ATTR_ASSIGN_RE.findall(token)) > MAX_ATTRIBUTES_PER_ELEMENT:
                    attr_violation = True
                if not token.endswith("/>"):
                    depth += 1
                    max_depth = max(max_depth, depth)
    if length - position > 0:
        tail = text[position:]
        if len(tail.encode("utf-8", errors="ignore")) > MAX_TEXT_NODE_BYTES:
            text_oversize = True
    return max_depth, elements, attr_violation or text_oversize


def _looks_like_xml_text(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped.startswith("<"):
        return False
    return "\x00" not in stripped[:4096]


def intake_bytes(raw: bytes) -> IntakeResult:
    """Produce InputSafetyEvidence plus the decoded canonical artifact text.

    Never raises on hostile input — every anomaly becomes evidence.
    """
    oversized = len(raw) > MAX_INPUT_BYTES
    text, detected, declared, decoded = _decode(raw)
    canonical_length = len(text.encode("utf-8")) if text is not None else 0

    dtd = bool(_DOCTYPE_RE.search(text)) if text is not None else False
    external_entities = (
        bool(_EXTERNAL_ENTITY_RE.search(text)) if text is not None else False
    )
    entity_expansion = False
    if text is not None:
        if _ENTITY_DECL_RE.search(text):
            entity_expansion = True
        else:
            for ref in _ENTITY_REF_RE.finditer(text):
                if ref.group(1) not in _BUILTIN_ENTITIES:
                    entity_expansion = True
                    break

    depth_ok = True
    resource_ok = True
    element_count = 0
    if decoded and text is not None:
        max_depth, element_count, resource_violation = _scan_structure(text)
        depth_ok = max_depth <= MAX_XML_DEPTH
        resource_ok = element_count <= MAX_XML_ELEMENTS and not resource_violation

    artifact: CanonicalBpmnArtifact | None = None
    if decoded and text is not None and _looks_like_xml_text(text):
        artifact = CanonicalBpmnArtifact(content=text)

    evidence = InputSafetyEvidence(
        original_byte_length=len(raw),
        canonical_utf8_byte_length=canonical_length,
        declared_encoding=declared,
        detected_encoding=detected,
        bom_present=detected is not None,
        decode_succeeded=decoded and text is not None,
        dtd_detected=dtd,
        external_entity_declarations_detected=external_entities,
        entity_expansion_beyond_builtins_detected=entity_expansion,
        depth_within_limit=depth_ok and resource_ok,
    )
    return IntakeResult(evidence=evidence, artifact=artifact, oversized=oversized)
