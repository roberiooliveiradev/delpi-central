"""ATLAS HML stage 74: read-only boot conflict audit and no-clobber review.

This is SOURCE-ONLY. No installation, tmpfiles invocation, subprocess, Docker,
systemd operations, key generation, or MCP tools. It never grants PREPARE/ACT.
A clean fixture is not evidence that the real host is safe to activate.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from .atlas_hml_b_stage71_readonly_preflight import _DIRECTORY_POLICY, _UNIT_NAMES, _SYSTEMD_LOCATIONS
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
class Stage74BootAudit:
    config_files_scanned: int
    config_dirs_present: int
    candidate_no_clobber: bool
    finding_codes: tuple[str, ...]
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
    """Walk all directory components without following symlinks."""
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
    """Bounded read from regular, stable inode; reject links/hardlinks."""
    if (
        type(name) is not str or not name.endswith(".conf")
        or name in (".", "..") or "/" in name or "\x00" in name
    ):
        raise Stage74AuditError("STAGE74_CONFIG_NAME_DENIED")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                 dir_fd=directory_fd)
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
        signature = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns,
                                st.st_mode, st.st_uid, st.st_gid)
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


def _line_finding(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#") or line.startswith(";"):
        return None
    parts = line.split(None, 2)
    if len(parts) < 2:
        return "TMPFILES_UNPARSEABLE_RULE" if "atlas-hml" in line else None
    op, path = parts[0], parts[1]
    if (
        "%" in path or "\\" in path
        or any(character in path for character in "*?[]")
    ):
        if path.startswith(("/run", "/var", "/%")) or "atlas-hml" in path:
            return "TMPFILES_DYNAMIC_RULE_REQUIRES_REVIEW"
        return None
    if path == "/" or not path.startswith("/") or "/../" in path:
        return "TMPFILES_UNVERIFIABLE_PATH"
    if "atlas-hml" in path:
        return "TMPFILES_ATLAS_PATH_ALREADY_DECLARED"
    for target in _TARGETS:
        if path == target or path.startswith(target + "/"):
            return "TMPFILES_TARGET_OVERLAP"
        if target.startswith(path.rstrip("/") + "/"):
            # Parent rules can have recursive ACL/removal/owner effects.
            # Ordinary d rules on /run or /var/lib remain reviewable,
            # never approval from this self-observation.
            return "TMPFILES_PARENT_RULE_REQUIRES_REVIEW"
    return None


def _scan_tmpfiles(root: Path) -> tuple[int, int, list[str]]:
    findings: list[str] = []
    total_files, present_dirs = 0, 0
    basename_seen: set[str] = set()
    for relative in _CONFIG_DIRS:
        fd = -1
        try:
            fd = _open_directory_at_root(root, relative)
        except FileNotFoundError:
            continue
        except (OSError, Stage74AuditError):
            findings.append("TMPFILES_CONFIG_DIRECTORY_UNVERIFIABLE")
            continue
        present_dirs += 1
        try:
            names = sorted(os.listdir(fd))
            if len(names) > _MAX_FILES:
                findings.append("TMPFILES_CONFIG_INVENTORY_TOO_LARGE")
                continue
            for name in names:
                if not name.endswith(".conf"):
                    continue
                total_files += 1
                if total_files > _MAX_FILES:
                    findings.append("TMPFILES_CONFIG_INVENTORY_TOO_LARGE")
                    break
                if name == _OUR_CONF:
                    findings.append("ATLAS_TMPFILES_CONF_NAME_ALREADY_PRESENT")
                if name in basename_seen:
                    findings.append("TMPFILES_BASENAME_PRECEDENCE_REVIEW")
                basename_seen.add(name)
                try:
                    content = _read_config(fd, name)
                except (OSError, Stage74AuditError):
                    findings.append("TMPFILES_CONFIG_UNREADABLE_OR_UNSTABLE")
                    continue
                for line in content.splitlines():
                    finding = _line_finding(line)
                    if finding is not None:
                        findings.append(finding)
        except (OSError, ValueError):
            findings.append("TMPFILES_CONFIG_INVENTORY_UNVERIFIABLE")
        finally:
            os.close(fd)
    return total_files, present_dirs, findings


def _scan_units(root: Path) -> list[str]:
    findings: list[str] = []
    for location in _SYSTEMD_LOCATIONS:
        try:
            fd = _open_directory_at_root(root, location)
        except FileNotFoundError:
            continue
        except (OSError, Stage74AuditError):
            findings.append("SYSTEMD_UNIT_DIRECTORY_UNVERIFIABLE")
            continue
        try:
            for name in _OUR_UNITS:
                try:
                    os.stat(name, dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                except OSError:
                    findings.append("SYSTEMD_UNIT_NAME_UNVERIFIABLE")
                else:
                    findings.append("ATLAS_SYSTEMD_UNIT_ALREADY_PRESENT")
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
    # Never allow a clean scan to upgrade a fixture or live self-report.
    findings.append("HOST_ATTESTATION_NOT_INDEPENDENT")
    return Stage74BootAudit(
        config_files_scanned=count, config_dirs_present=present_dirs,
        candidate_no_clobber=no_clobber,
        finding_codes=tuple(dict.fromkeys(findings)),
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
        "schema": "atlas.hml.stage74.boot-audit.v1",
        "observation_kind": "operator_self_observation",
        **asdict(report),
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
