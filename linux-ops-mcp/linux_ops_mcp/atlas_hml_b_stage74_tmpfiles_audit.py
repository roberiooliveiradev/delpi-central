"""ATLAS HML stage 74/76: read-only tmpfiles audit with precise classification.

SOURCE-ONLY. No installation, tmpfiles invocation against the live host root,
Docker, key generation or MCP tools. Never grants PREPARE/ACT. A clean scan is
not independent host attestation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from .atlas_hml_b_stage71_readonly_preflight import (
    _DIRECTORY_POLICY, _UNIT_NAMES, _SYSTEMD_LOCATIONS,
)
from .atlas_hml_b_stage73_boot_guard import render_stage73_tmpfiles_payload

_CONFIG_DIRS = (
    "etc/tmpfiles.d",
    "run/tmpfiles.d",
    "usr/local/lib/tmpfiles.d",
    "usr/lib/tmpfiles.d",
)
_OUR_CONF = "atlas-hml-runtime-layout.conf"
_OUR_UNITS = (*_UNIT_NAMES, "atlas-hml-local-signer.socket", "atlas-hml-snapshot-presenter.socket")
_TARGETS = tuple(item[0] for item in _DIRECTORY_POLICY)
_MAX_FILES = 512
_MAX_BYTES = 262144
# Recursive / subtree-affecting type letters (systemd-tmpfiles.d man page).
_RECURSIVE_OPS = frozenset({"R", "Z", "T", "A", "H"})
_NONRECURSIVE_DIR_OPS = frozenset({"d", "D", "e", "q", "Q", "v", "F", "f", "w", "p", "L", "c", "b", "C", "x", "X", "r", "z", "t", "a", "h"})
_DYNAMIC_RE = re.compile(r"[%*?\[\]\\]")
_BLOCKS = (
    "STAGE74_READONLY_AUDIT_NOT_INDEPENDENT",
    "TMPFILES_BOOT_RECREATION_NOT_ATTESTED",
    "TMPFILES_CONFIG_ORDER_NOT_VERIFIED_BY_SYSTEMD",
    "SYSTEMD_RUNTIME_AND_EFFECTIVE_APPARMOR_NOT_ATTESTED",
    "DOCKER_ALTERNATE_ENDPOINTS_AND_FDS_NOT_ATTESTED",
    "KEY_BOOTSTRAP_GEN1_EXTERNAL_ANCHOR_GLPI_PENDING",
    "SEC_01_TO_10_PENDING",
    "OPERATIONAL_CHANGE_CONTROL_REQUIRED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class Stage74AuditError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Stage74Finding:
    code: str
    classification: str  # critical | review | info | residual
    source_file: str
    line_number: int
    directive: str
    path: str
    rationale: str
    human_review_required: bool


@dataclass(frozen=True, slots=True)
class Stage74BootAudit:
    config_files_scanned: int
    config_dirs_present: int
    candidate_no_clobber: bool
    findings: tuple[Stage74Finding, ...]
    finding_codes: tuple[str, ...]
    critical_codes: tuple[str, ...]
    info_codes: tuple[str, ...]
    status: str = "blocked"
    host_attested: bool = False
    boot_recreated: bool = False
    installation_authorized: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def review_no_clobber_candidate() -> bool:
    """Verify create-only mode, owner and group on all five exact d entries."""
    payload = render_stage73_tmpfiles_payload()
    lines = [line.split() for line in payload.splitlines() if line.startswith("d ")]
    if len(lines) != len(_TARGETS) or tuple(line[1] for line in lines) != _TARGETS:
        raise Stage74AuditError("STAGE74_LAYOUT_DRIFT")
    for line in lines:
        if (
            len(line) != 6
            or line[0] != "d" or line[5] != "-"
            or any(not field.startswith(":") for field in line[2:5])
            or line[2][1:] not in ("0750", "02750", "0700")
            or any(not field[1:] for field in line[3:5])
        ):
            raise Stage74AuditError("STAGE74_CLOBBERABLE_RULE_DENIED")
    return True


def _open_directory_at_root(root: Path, relative: str) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(root, flags)
    try:
        for component in relative.split("/"):
            if component in ("", ".", ".."):
                raise Stage74AuditError("STAGE74_CONFIG_PATH_DENIED")
            next_fd = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read_config(directory_fd: int, name: str) -> str:
    if (
        type(name) is not str or not name.endswith(".conf")
        or name in (".", "..") or "/" in name or "\x00" in name
    ):
        raise Stage74AuditError("STAGE74_CONFIG_NAME_DENIED")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory_fd)
    try:
        before = os.fstat(fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or not 0 <= before.st_size <= _MAX_BYTES
        ):
            raise Stage74AuditError("STAGE74_CONFIG_TYPE_OR_SIZE_DENIED")
        raw = os.read(fd, _MAX_BYTES + 1)
        after = os.fstat(fd)
        named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)

        def signature(st: os.stat_result) -> tuple[int, ...]:
            return (
                st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns,
                st.st_mode, st.st_uid, st.st_gid,
            )

        if (
            len(raw) > _MAX_BYTES or b"\x00" in raw
            or signature(before) != signature(after)
            or signature(after) != signature(named)
        ):
            raise Stage74AuditError("STAGE74_CONFIG_CHANGED_OR_INVALID")
        try:
            return raw.decode("utf-8", errors="strict")
        except UnicodeError:
            raise Stage74AuditError("STAGE74_CONFIG_ENCODING_DENIED") from None
    finally:
        os.close(fd)


def _norm_path(path: str) -> str:
    if path != "/" and path.endswith("/"):
        return path.rstrip("/")
    return path


def _static_prefix(path: str) -> str:
    """Longest leading absolute prefix before the first dynamic token."""
    match = _DYNAMIC_RE.search(path)
    if match is None:
        return _norm_path(path)
    prefix = path[: match.start()]
    if not prefix.startswith("/"):
        return ""
    if prefix != "/" and prefix.endswith("/"):
        prefix = prefix.rstrip("/")
    return prefix or "/"


def _path_is_atlas_declared(path: str) -> bool:
    return "atlas-hml" in path


def _overlaps_target(path: str) -> bool:
    normalized = _norm_path(path)
    for target in _TARGETS:
        if normalized == target or normalized.startswith(target + "/"):
            return True
    return False


def _is_ancestor_of_target(path: str) -> bool:
    normalized = _norm_path(path)
    if normalized in {"", "/"}:
        return True
    for target in _TARGETS:
        if target.startswith(normalized + "/"):
            return True
    return False


def _dynamic_may_hit_atlas(path: str) -> bool | None:
    """True=possible hit, False=out of scope, None=unclassifiable."""
    if "atlas-hml" in path:
        return True
    prefix = _static_prefix(path)
    if prefix in {"", "/"}:
        # Specifiers at the root (e.g. /%T/...) cannot be proven out of scope.
        return None
    if _overlaps_target(prefix) or _is_ancestor_of_target(prefix):
        return True
    # Prefix is a sibling tree (journal, tmp, log, …).
    for target in _TARGETS:
        if prefix.startswith(target + "/") or target.startswith(prefix + "/"):
            return True
    return False


def classify_tmpfiles_line(
    *,
    source_file: str,
    line_number: int,
    line: str,
) -> Stage74Finding | None:
    """Classify one tmpfiles rule; fail-closed when semantics are ambiguous."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith(";"):
        return None
    parts = stripped.split()
    if len(parts) < 2:
        if "atlas-hml" in stripped:
            return Stage74Finding(
                code="TMPFILES_UNPARSEABLE_RULE",
                classification="critical",
                source_file=source_file,
                line_number=line_number,
                directive="",
                path="",
                rationale="Unparseable rule mentioning atlas-hml",
                human_review_required=True,
            )
        return None
    op, path = parts[0], parts[1]
    type_letter = op[:1]
    if path == "/" or not path.startswith("/") or "/../" in path:
        return Stage74Finding(
            code="TMPFILES_UNVERIFIABLE_PATH",
            classification="review",
            source_file=source_file,
            line_number=line_number,
            directive=op,
            path=path,
            rationale="Path is unverifiable or unsafe",
            human_review_required=True,
        )

    dynamic = _DYNAMIC_RE.search(path) is not None
    if dynamic:
        hit = _dynamic_may_hit_atlas(path)
        if hit is True:
            return Stage74Finding(
                code="TMPFILES_DYNAMIC_ATLAS_AMBIGUOUS",
                classification="critical",
                source_file=source_file,
                line_number=line_number,
                directive=op,
                path=path,
                rationale="Dynamic path may expand onto ATLAS exclusive trees",
                human_review_required=True,
            )
        if hit is False:
            return Stage74Finding(
                code="TMPFILES_OS_DYNAMIC_OUT_OF_SCOPE_INFO",
                classification="info",
                source_file=source_file,
                line_number=line_number,
                directive=op,
                path=path,
                rationale="Dynamic OS path prefix cannot reach ATLAS exclusive directories",
                human_review_required=False,
            )
        return Stage74Finding(
            code="TMPFILES_UNCLASSIFIED_FAIL_CLOSED",
            classification="critical",
            source_file=source_file,
            line_number=line_number,
            directive=op,
            path=path,
            rationale="Dynamic path cannot be proven out of ATLAS scope",
            human_review_required=True,
        )

    if _path_is_atlas_declared(path) or _overlaps_target(path):
        return Stage74Finding(
            code="TMPFILES_ATLAS_PATH_ALREADY_DECLARED",
            classification="critical",
            source_file=source_file,
            line_number=line_number,
            directive=op,
            path=path,
            rationale="Rule targets an ATLAS exclusive path or descendant",
            human_review_required=True,
        )

    if _is_ancestor_of_target(path):
        if type_letter in _RECURSIVE_OPS:
            return Stage74Finding(
                code="TMPFILES_RECURSIVE_PARENT_CONFLICT",
                classification="critical",
                source_file=source_file,
                line_number=line_number,
                directive=op,
                path=path,
                rationale="Recursive operation on an ancestor of ATLAS directories",
                human_review_required=True,
            )
        if type_letter in _NONRECURSIVE_DIR_OPS or type_letter.isalpha():
            return Stage74Finding(
                code="TMPFILES_OS_PARENT_NONRECURSIVE_INFO",
                classification="info",
                source_file=source_file,
                line_number=line_number,
                directive=op,
                path=path,
                rationale=(
                    "Non-recursive parent rule affects only the ancestor inode; "
                    "not an exclusive ATLAS directory conflict"
                ),
                human_review_required=False,
            )
        return Stage74Finding(
            code="TMPFILES_UNCLASSIFIED_FAIL_CLOSED",
            classification="critical",
            source_file=source_file,
            line_number=line_number,
            directive=op,
            path=path,
            rationale="Unknown type letter on ATLAS ancestor; fail-closed",
            human_review_required=True,
        )
    return None


def _scan_tmpfiles(root: Path) -> tuple[int, int, list[Stage74Finding]]:
    findings: list[Stage74Finding] = []
    total_files, present_dirs = 0, 0
    basename_locations: dict[str, list[str]] = {}
    for relative in _CONFIG_DIRS:
        fd = -1
        try:
            fd = _open_directory_at_root(root, relative)
        except FileNotFoundError:
            continue
        except (OSError, Stage74AuditError):
            findings.append(Stage74Finding(
                code="TMPFILES_CONFIG_DIRECTORY_UNVERIFIABLE",
                classification="review",
                source_file=relative,
                line_number=0,
                directive="",
                path="",
                rationale="Config directory unreadable without following symlinks",
                human_review_required=True,
            ))
            continue
        present_dirs += 1
        try:
            names = sorted(os.listdir(fd))
            if len(names) > _MAX_FILES:
                findings.append(Stage74Finding(
                    code="TMPFILES_CONFIG_INVENTORY_TOO_LARGE",
                    classification="review",
                    source_file=relative,
                    line_number=0,
                    directive="",
                    path="",
                    rationale="Too many entries under tmpfiles.d",
                    human_review_required=True,
                ))
                continue
            for name in names:
                if not name.endswith(".conf"):
                    continue
                total_files += 1
                if total_files > _MAX_FILES:
                    findings.append(Stage74Finding(
                        code="TMPFILES_CONFIG_INVENTORY_TOO_LARGE",
                        classification="review",
                        source_file=relative,
                        line_number=0,
                        directive="",
                        path="",
                        rationale="Inventory exceeded bound",
                        human_review_required=True,
                    ))
                    break
                source = f"{relative}/{name}"
                if name == _OUR_CONF:
                    findings.append(Stage74Finding(
                        code="ATLAS_TMPFILES_CONF_NAME_ALREADY_PRESENT",
                        classification="critical",
                        source_file=source,
                        line_number=0,
                        directive="",
                        path="",
                        rationale="Reserved ATLAS tmpfiles basename already present",
                        human_review_required=True,
                    ))
                basename_locations.setdefault(name, []).append(source)
                try:
                    content = _read_config(fd, name)
                except (OSError, Stage74AuditError):
                    findings.append(Stage74Finding(
                        code="TMPFILES_CONFIG_UNREADABLE_OR_UNSTABLE",
                        classification="review",
                        source_file=source,
                        line_number=0,
                        directive="",
                        path="",
                        rationale="Config not a stable regular file (symlink/hardlink/size)",
                        human_review_required=True,
                    ))
                    continue
                for index, line in enumerate(content.splitlines(), start=1):
                    finding = classify_tmpfiles_line(
                        source_file=source, line_number=index, line=line,
                    )
                    if finding is not None:
                        findings.append(finding)
        except (OSError, ValueError):
            findings.append(Stage74Finding(
                code="TMPFILES_CONFIG_INVENTORY_UNVERIFIABLE",
                classification="review",
                source_file=relative,
                line_number=0,
                directive="",
                path="",
                rationale="Failed to inventory directory",
                human_review_required=True,
            ))
        finally:
            os.close(fd)

    for name, locations in sorted(basename_locations.items()):
        if len(locations) < 2:
            continue
        # Precedence matter only elevates when any duplicate carries ATLAS risk.
        atlas_risk = any(
            finding.source_file in locations
            and finding.classification in {"critical", "review"}
            and finding.code not in {
                "TMPFILES_OS_PARENT_NONRECURSIVE_INFO",
                "TMPFILES_OS_DYNAMIC_OUT_OF_SCOPE_INFO",
                "TMPFILES_BASENAME_PRECEDENCE_INFO",
            }
            for finding in findings
        )
        findings.append(Stage74Finding(
            code=(
                "TMPFILES_BASENAME_PRECEDENCE_REVIEW"
                if atlas_risk else "TMPFILES_BASENAME_PRECEDENCE_INFO"
            ),
            classification="review" if atlas_risk else "info",
            source_file=",".join(locations),
            line_number=0,
            directive="",
            path=name,
            rationale=(
                "Duplicate basename across tmpfiles.d search paths; "
                + (
                    "atlas-relevant content present — human precedence review"
                    if atlas_risk
                    else "no ATLAS exclusive overlap detected in scanned content"
                )
            ),
            human_review_required=atlas_risk,
        ))
    return total_files, present_dirs, findings


def _scan_units(root: Path) -> list[Stage74Finding]:
    findings: list[Stage74Finding] = []
    for location in _SYSTEMD_LOCATIONS:
        try:
            fd = _open_directory_at_root(root, location)
        except FileNotFoundError:
            continue
        except (OSError, Stage74AuditError):
            findings.append(Stage74Finding(
                code="SYSTEMD_UNIT_DIRECTORY_UNVERIFIABLE",
                classification="review",
                source_file=location,
                line_number=0,
                directive="",
                path="",
                rationale="systemd unit directory unreadable",
                human_review_required=True,
            ))
            continue
        try:
            for name in _OUR_UNITS:
                try:
                    os.stat(name, dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                except OSError:
                    findings.append(Stage74Finding(
                        code="SYSTEMD_UNIT_NAME_UNVERIFIABLE",
                        classification="review",
                        source_file=f"{location}/{name}",
                        line_number=0,
                        directive="",
                        path=name,
                        rationale="Unit name unstatable",
                        human_review_required=True,
                    ))
                else:
                    findings.append(Stage74Finding(
                        code="ATLAS_SYSTEMD_UNIT_ALREADY_PRESENT",
                        classification="critical",
                        source_file=f"{location}/{name}",
                        line_number=0,
                        directive="",
                        path=name,
                        rationale="ATLAS unit already present on scanned root",
                        human_review_required=True,
                    ))
        finally:
            os.close(fd)
    return findings


def audit_stage74_boot_config(*, root: Path, host_readonly: bool = False) -> Stage74BootAudit:
    """Bounded self-observation; root=/ requires explicit read-only consent."""
    if (
        type(root) is not type(Path("/")) or not root.is_absolute()
        or root.is_symlink() or not root.is_dir()
        or type(host_readonly) is not bool
        or (root == Path("/") and not host_readonly)
    ):
        raise Stage74AuditError("STAGE74_EXPLICIT_ROOT_REQUIRED")
    no_clobber = review_no_clobber_candidate()
    count, present_dirs, findings = _scan_tmpfiles(root)
    findings += _scan_units(root)
    findings.append(Stage74Finding(
        code="HOST_ATTESTATION_NOT_INDEPENDENT",
        classification="residual",
        source_file="",
        line_number=0,
        directive="",
        path="",
        rationale="Self-observation is never independent host attestation",
        human_review_required=True,
    ))
    codes = tuple(dict.fromkeys(item.code for item in findings))
    critical = tuple(
        dict.fromkeys(
            item.code for item in findings if item.classification == "critical"
        )
    )
    info = tuple(
        dict.fromkeys(item.code for item in findings if item.classification == "info")
    )
    return Stage74BootAudit(
        config_files_scanned=count,
        config_dirs_present=present_dirs,
        candidate_no_clobber=no_clobber,
        findings=tuple(findings),
        finding_codes=codes,
        critical_codes=critical,
        info_codes=info,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ATLAS Stage74 read-only boot audit")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--fixture-root", type=Path, metavar="ABSOLUTE_DIR")
    scope.add_argument("--host-readonly", action="store_true")
    args = parser.parse_args(argv)
    root = Path("/") if args.host_readonly else args.fixture_root
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        parser.error("STAGE74_ROOT_DENIED")
    report = audit_stage74_boot_config(root=root, host_readonly=args.host_readonly)
    print(json.dumps({
        "schema": "atlas.hml.stage74.boot-audit.v2",
        "observation_kind": "operator_self_observation",
        **asdict(report),
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
