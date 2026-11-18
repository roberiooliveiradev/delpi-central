"""Static review of ATLAS HML candidate systemd units (never auto-installed).

Candidates live under linux-ops-mcp/candidate-units/*.candidate and MUST:
- use extension .candidate (not .service/.socket/.timer)
- include RefuseManualStart=yes
- include an impossible ConditionPathExists sentinel
- omit [Install]
- keep ExecStart as /usr/bin/false until a later authorized packaging step

Passing this review never attests host isolation or authorizes installation.
"""
from __future__ import annotations

import configparser
import io
from dataclasses import dataclass
from pathlib import Path

_DIR = Path(__file__).resolve().parents[1] / "candidate-units"
_SENTINEL = "/run/atlas-hml-candidate/REVIEW-ONLY-NEVER-CREATE"
_REQUIRED_FILES = frozenset({
    "atlas-hml-snapshot-producer.service.candidate",
    "atlas-hml-snapshot-producer.timer.candidate",
    "atlas-hml-local-signer.service.candidate",
    "atlas-hml-nonroot-bridge.service.candidate",
    "atlas-hml-snapshot-presenter.service.candidate",
    "atlas-hml-runtime-layout.tmpfiles.candidate",
})
_HARDENED = {
    "NoNewPrivileges": "yes",
    "ProtectSystem": "strict",
    "ProtectHome": "yes",
    "PrivateTmp": "yes",
    "PrivateDevices": "yes",
    "RestrictAddressFamilies": "AF_UNIX",
    "UMask": "0077",
}
_BLOCKS = (
    "CANDIDATE_UNITS_NOT_INSTALLED",
    "AUTO_DEPLOY_MUST_IGNORE_CANDIDATE_UNITS",
    "HOST_SANDBOX_NOT_ATTESTED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLCandidateUnitError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLCandidateUnitReview:
    status: str = "blocked"
    files_reviewed: int = 0
    install_sections_present: bool = False
    auto_enable_possible: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _parse(source: str) -> dict[str, dict[str, str]]:
    parser = configparser.ConfigParser(
        interpolation=None, strict=True, allow_no_value=False,
    )
    parser.optionxform = str
    try:
        parser.read_file(io.StringIO(source))
    except configparser.Error:
        raise HMLCandidateUnitError("HML_CANDIDATE_UNIT_PARSE_DENIED") from None
    return {
        section: dict(parser.items(section, raw=True))
        for section in parser.sections()
    }


def review_candidate_unit_sources(
    sources: dict[str, str] | None = None,
) -> HMLCandidateUnitReview:
    if sources is None:
        sources = {}
        if not _DIR.is_dir():
            raise HMLCandidateUnitError("HML_CANDIDATE_DIR_MISSING")
        for path in sorted(_DIR.glob("*.candidate")):
            sources[path.name] = path.read_text(encoding="utf-8")
    if type(sources) is not dict or set(sources) != _REQUIRED_FILES:
        raise HMLCandidateUnitError("HML_CANDIDATE_SET_DENIED")
    for name, text in sources.items():
        if type(name) is not str or not name.endswith(".candidate"):
            raise HMLCandidateUnitError("HML_CANDIDATE_EXTENSION_DENIED")
        if name.endswith((".service", ".socket", ".timer")):
            raise HMLCandidateUnitError("HML_CANDIDATE_EXTENSION_DENIED")
        if name.endswith(".tmpfiles.candidate"):
            if _SENTINEL not in text or "atlas-hml" not in text:
                raise HMLCandidateUnitError("HML_CANDIDATE_TMPFILES_DENIED")
            if "[Install]" in text:
                raise HMLCandidateUnitError("HML_CANDIDATE_INSTALL_FORBIDDEN")
            continue
        parsed = _parse(text)
        if "Install" in parsed:
            raise HMLCandidateUnitError("HML_CANDIDATE_INSTALL_FORBIDDEN")
        unit = parsed.get("Unit")
        if type(unit) is not dict:
            raise HMLCandidateUnitError("HML_CANDIDATE_UNIT_SECTION_DENIED")
        if unit.get("RefuseManualStart") != "yes":
            raise HMLCandidateUnitError("HML_CANDIDATE_REFUSE_MANUAL_REQUIRED")
        if unit.get("ConditionPathExists") != _SENTINEL:
            raise HMLCandidateUnitError("HML_CANDIDATE_SENTINEL_REQUIRED")
        if "Service" in parsed:
            service = parsed["Service"]
            if service.get("ExecStart") != "/usr/bin/false":
                raise HMLCandidateUnitError("HML_CANDIDATE_EXEC_MUST_REMAIN_FALSE")
            for key, value in _HARDENED.items():
                if service.get(key) != value:
                    raise HMLCandidateUnitError("HML_CANDIDATE_HARDENING_DENIED")
            if "docker.sock" not in service.get("InaccessiblePaths", "") and (
                "signer" in name or "bridge" in name or "presenter" in name
            ):
                raise HMLCandidateUnitError("HML_CANDIDATE_DOCKER_ISOLATION_DENIED")
        if "Socket" in parsed:
            raise HMLCandidateUnitError("HML_CANDIDATE_SIGNER_SOCKET_SECTION_FORBIDDEN")
        if "Timer" in parsed:
            timer = parsed["Timer"]
            if timer.get("Unit") != "atlas-hml-snapshot-producer.service":
                raise HMLCandidateUnitError("HML_CANDIDATE_TIMER_TARGET_DENIED")
    return HMLCandidateUnitReview(files_reviewed=len(sources))
