"""Strict P4 validator for UNTRUSTED local Windows readiness observations.

A readiness observation never grants enrollment, key trust, S2S or remote access.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

KIND = "delpi-it-remote-p4-readiness"
ORIGIN = "unauthenticated-local-readonly"
FIELDS = frozenset(("schema_version", "kind", "origin", "collected_at", "platform", "tpm", "secure_boot", "hardware_attested", "key_bound", "activation_authorized"))
TPM_FIELDS = frozenset(("present", "ready", "spec"))
UTC_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
MAX_REPORT_SIZE = 2048
MAX_AGE = timedelta(minutes=15)
FUTURE_SKEW = timedelta(minutes=2)


@dataclass(frozen=True)
class Readiness:
    status: str
    reasons: tuple[str, ...]
    attested: bool = False
    enrollment_authorized: bool = False


def _invalid(reason: str) -> Readiness:
    return Readiness("INVALID", (reason,))


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate-json-field")
        result[key] = value
    return result


def evaluate_report(raw: str, *, now: datetime | None = None) -> Readiness:
    """No IO: reject identifiers, extra fields and forged approval claims."""
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_REPORT_SIZE:
        return _invalid("invalid-size")
    try:
        report = json.loads(raw, object_pairs_hook=_unique_pairs)
    except (TypeError, ValueError, UnicodeError):
        return _invalid("invalid-json")
    if not isinstance(report, dict) or report.keys() != FIELDS:
        return _invalid("unexpected-fields")
    if (type(report["schema_version"]) is not int or report["schema_version"] != 1
            or report["kind"] != KIND or report["origin"] != ORIGIN):
        return _invalid("invalid-origin-or-version")
    if (report["hardware_attested"] is not False
            or report["key_bound"] is not False
            or report["activation_authorized"] is not False):
        return _invalid("unauthorized-claim")
    collected = report["collected_at"]
    if not isinstance(collected, str) or not UTC_SECOND.fullmatch(collected):
        return _invalid("invalid-timestamp")
    try:
        moment = datetime.fromisoformat(collected.replace("Z", "+00:00"))
    except ValueError:
        return _invalid("invalid-timestamp")
    clock = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(clock, datetime) or clock.tzinfo is None or clock.utcoffset() is None:
        return _invalid("invalid-clock")
    clock = clock.astimezone(timezone.utc)
    if moment < clock - MAX_AGE or moment > clock + FUTURE_SKEW:
        return _invalid("stale-or-future-report")
    platform, tpm, boot = report["platform"], report["tpm"], report["secure_boot"]
    if type(platform) is not str or platform not in ("windows", "non_windows"):
        return _invalid("invalid-platform")
    if not isinstance(tpm, dict) or tpm.keys() != TPM_FIELDS:
        return _invalid("invalid-tpm-fields")
    if (type(tpm["present"]) is not str or tpm["present"] not in ("yes", "no", "unknown")
            or type(tpm["ready"]) is not str or tpm["ready"] not in ("yes", "no", "unknown")
            or type(tpm["spec"]) is not str or tpm["spec"] not in ("2.0", "1.2", "unknown")
            or type(boot) is not str or boot not in ("enabled", "disabled", "unknown")):
        return _invalid("invalid-capability")
    if ((tpm["present"] == "no" and (tpm["ready"] == "yes" or tpm["spec"] != "unknown"))
            or (tpm["present"] == "unknown" and tpm["spec"] != "unknown")):
        return _invalid("inconsistent-capability")
    if platform == "non_windows":
        if tpm != {"present": "unknown", "ready": "unknown", "spec": "unknown"} or boot != "unknown":
            return _invalid("non-windows-must-not-report-tpm")
        return Readiness("NOT_READY", ("not-windows",))
    if (tpm["present"] == "no" or tpm["ready"] == "no" or tpm["spec"] == "1.2" or boot == "disabled"):
        return Readiness("NOT_READY", ("missing-security-prerequisites",))
    if (tpm["present"] != "yes" or tpm["ready"] != "yes" or tpm["spec"] != "2.0" or boot != "enabled"):
        return Readiness("INCONCLUSIVE", ("probe-unavailable-or-privilege-limited",))
    return Readiness("CANDIDATE", ("hml-cryptographic-attestation-still-required",))
