"""ATLAS P2.2h.2ab-ad: manually invoked, read-only HML host preflight.

Runnable with: PYTHONPATH=linux-ops-mcp python3 -m linux_ops_mcp.atlas_hml_local_probe

NEVER acts as a deploy gate, PREPARE, ACT, proof of host attestation or
permission to connect to a Docker socket. Refuses root, privileged group or
writable checkout before even reading Git or the optional fixed HML proxy.
The Docker proxy must be provisioned and independently audited separately;
a UNIX socket name and GET-only Python code DO NOT prove proxy restrictions.
No HTTP/MCP routes, keys, DB, registry, network over TCP, or mutations.
"""
from __future__ import annotations

import asyncio
import grp
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx

from .atlas_hml_git_head_peek import GitHeadMetadataPeek, GitHeadPeekError
from .atlas_hml_uds_policy import (
    HMLUDSPolicyError, verify_socket_metadata,
)
from .deploy_git_checkout_readonly import (
    GitCheckoutReadError, GitCheckoutReadOnlyObserver, _ROOT as _CHECKOUT,
)
from .deploy_host_source import (
    DockerReadOnlyInspect, HostSourceError, RuntimeTarget,
)

_TARGET = RuntimeTarget(
    environment="hml", service_id="public-hub", host_id="srv-api-pilot",
    compose_project="delpi-hml", container_name="delpi-hml-public-hub",
)
_PROXY_SOCKET = Path("/run/atlas-hml-readonly/inspect.sock")
_RAW_SOCKETS = (Path("/var/run/docker.sock"), Path("/run/docker.sock"))
_PRIVILEGED = frozenset(("root", "docker", "sudo", "wheel", "lxd", "podman"))
_ALWAYS_BLOCKS = (
    "HOST_OS_IDENTITY_NOT_ATTESTED",
    "HML_PROXY_POLICY_NOT_INDEPENDENTLY_ATTESTED",
    "GIT_IGNORED_FILES_NOT_MEASURED",
    "GIT_FILESYSTEM_SNAPSHOT_NOT_ATOMIC",
    "COLLECTOR_TRANSPORT_NOT_ATTESTED",
    "JOURNAL_CHALLENGE_NOT_CONSUMED",
    "BACKUP_RESTORE_AND_ROLLBACK_NOT_ATTESTED",
    "CORE_PREPARE_NOT_AUTHORIZED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


@dataclass(frozen=True, slots=True)
class LocalOSObservation:
    uid: int
    euid: int
    groups: tuple[str, ...]
    checkout_writable: bool


@dataclass(frozen=True, slots=True)
class LocalHMLProbeReport:
    """No raw Docker JSON, paths, keys, usernames or secrets."""

    status: str
    blocks: tuple[str, ...]
    environment: str = "hml"
    service_id: str = "public-hub"
    git_head: str | None = None
    git_branch: str | None = None
    git_clean_nonignored: bool | None = None
    git_observation_method: str | None = None
    docker_image_id: str | None = None
    docker_running: bool | None = None
    docker_healthy: bool | None = None
    observed_at: str | None = None
    collector_identity_attested: bool = False
    docker_proxy_readonly_attested: bool = False
    checkout_integrity_attested: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


class HMLProbeError(Exception):
    """Finite error strings only; never print raw filesystem/Docker errors."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def read_local_os() -> LocalOSObservation:
    """Read only the OS process identity and fixed-checkout write access."""
    try:
        groups = tuple(sorted({
            grp.getgrgid(gid).gr_name for gid in {*os.getgroups(), os.getegid()}
        }))
        return LocalOSObservation(
            uid=os.getuid(), euid=os.geteuid(), groups=groups,
            checkout_writable=os.access(_CHECKOUT, os.W_OK),
        )
    except (OSError, KeyError):
        raise HMLProbeError("OS_INSPECTION_UNAVAILABLE") from None


def account_blocks(identity: object) -> tuple[str, ...]:
    if (
        type(identity) is not LocalOSObservation
        or type(identity.uid) is not int
        or type(identity.euid) is not int
        or type(identity.groups) is not tuple
        or not all(type(g) is str for g in identity.groups)
        or type(identity.checkout_writable) is not bool
    ):
        raise HMLProbeError("OS_INSPECTION_INVALID")
    blocks: list[str] = []
    if identity.uid == 0 or identity.euid == 0 or identity.uid != identity.euid:
        blocks.append("ACCOUNT_ROOT_OR_SETUID")
    if _PRIVILEGED.intersection(identity.groups):
        blocks.append("ACCOUNT_PRIVILEGED_GROUP")
    if identity.checkout_writable:
        blocks.append("ACCOUNT_CAN_MODIFY_CHECKOUT")
    return tuple(blocks)


def _stat_fixed_proxy(
    *, _test_owner_uid: int | None = None,
    _test_socket_gid: int | None = None,
    _test_raw_sockets: tuple[Path, ...] | None = None,
) -> None:
    """Use the shared fail-closed policy before any Docker projection GET.

    Overrides are solely for disposable tests and are never accepted by the
    CLI, MCP or HTTP. Real fixed-path verification requires root + atlas-hml.
    """
    try:
        options: dict[str, object] = {"path": _PROXY_SOCKET}
        if _test_owner_uid is not None:
            options["owner_uid"] = _test_owner_uid
        if _test_socket_gid is not None:
            options["socket_gid"] = _test_socket_gid
        if _test_raw_sockets is not None:
            options["raw_sockets"] = _test_raw_sockets
        verify_socket_metadata(**options)
    except HMLUDSPolicyError as exc:
        raise HMLProbeError(exc.code) from None

def fixed_proxy_inspector() -> DockerReadOnlyInspect:
    """Use only a separate, operator-provisioned UNIX socket, never TCP.

    Does not start a proxy, bind a socket, or contact Docker at construction.
    """
    _stat_fixed_proxy()
    return DockerReadOnlyInspect(
        transport=httpx.AsyncHTTPTransport(uds=str(_PROXY_SOCKET), retries=0),
    )


async def inspect_hml_local(
    *,
    identity: LocalOSObservation,
    observer: GitCheckoutReadOnlyObserver,
    inspector: DockerReadOnlyInspect | None,
    proxy_error: str | None = None,
    metadata_only: bool = False,
    metadata_reader: GitHeadMetadataPeek | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> LocalHMLProbeReport:
    """Observe HML once, always blocked. Injections are for isolated CI only."""
    account = account_blocks(identity)
    now = clock()
    if (
        type(now) is not datetime or now.tzinfo is None
        or now.utcoffset() is None
    ):
        raise HMLProbeError("HML_PROBE_CLOCK_INVALID")
    blocks = list((*_ALWAYS_BLOCKS, *account))
    info: dict[str, object] = {}
    if account:
        # Even Git status is skipped if the identity is too privileged.
        blocks.append("HOST_OBSERVATION_REFUSED_UNSAFE_ACCOUNT")
    else:
        if type(metadata_only) is not bool:
            raise HMLProbeError("HML_GIT_MODE_INVALID")
        if metadata_only:
            # A shared, group-writable host checkout is not a trusted Git
            # execution source. Read only HEAD/main ref; NEVER run git status,
            # safe.directory bypass, local Git config, hooks or filters.
            if type(metadata_reader) is not GitHeadMetadataPeek:
                blocks.append("HML_GIT_METADATA_READER_INVALID")
            else:
                try:
                    meta = metadata_reader.read()
                    info.update(
                        git_head=meta.head_sha,
                        git_branch=meta.branch,
                        git_observation_method=meta.source,
                    )
                    blocks.extend((
                        "HML_GIT_METADATA_ONLY_UNTRUSTED",
                        "HML_GIT_STATUS_NOT_CHECKED",
                    ))
                except GitHeadPeekError:
                    blocks.append("HML_GIT_METADATA_UNAVAILABLE")
                except Exception:
                    blocks.append("HML_GIT_METADATA_UNAVAILABLE")
        elif type(observer) is not GitCheckoutReadOnlyObserver:
            blocks.append("GIT_OBSERVER_INVALID")
        else:
            try:
                git = observer.read(target=_TARGET)
                info.update(
                    git_head=git.head_sha,
                    git_branch=git.branch,
                    git_clean_nonignored=git.tracked_and_untracked_clean,
                    git_observation_method="git_status_local_untrusted",
                )
                if not git.tracked_and_untracked_clean:
                    blocks.append("HML_CHECKOUT_DIRTY")
                if git.branch != "main":
                    blocks.append("HML_CHECKOUT_NOT_MAIN")
            except GitCheckoutReadError:
                blocks.append("HML_GIT_OBSERVATION_UNAVAILABLE")
            except Exception:
                blocks.append("HML_GIT_OBSERVATION_UNAVAILABLE")

        if inspector is None:
            blocks.append(proxy_error or "HML_PROXY_NOT_CONFIGURED")
        elif type(inspector) is not DockerReadOnlyInspect:
            blocks.append("HML_PROXY_INSPECTOR_INVALID")
        else:
            try:
                runtime = await inspector.inspect(_TARGET)
                info.update(
                    docker_image_id=runtime.image_id,
                    docker_running=runtime.running,
                    docker_healthy=runtime.healthy,
                )
                if not runtime.running or not runtime.healthy:
                    blocks.append("HML_CONTAINER_NOT_HEALTHY")
            except HostSourceError:
                blocks.append("HML_DOCKER_READ_UNAVAILABLE")
            except Exception:
                blocks.append("HML_DOCKER_READ_UNAVAILABLE")

    return LocalHMLProbeReport(
        status="blocked",
        blocks=tuple(dict.fromkeys(blocks)),
        observed_at=now.astimezone(timezone.utc).isoformat(),
        **info,
    )


def main() -> int:
    """One explicit, non-mutating invocation. Exit 0 means report printed ONLY."""
    try:
        ident = read_local_os()
        # Do not inspect or connect to any socket under a privileged identity.
        if account_blocks(ident):
            inspector, error = None, None
        else:
            try:
                inspector, error = fixed_proxy_inspector(), None
            except HMLProbeError as exc:
                inspector, error = None, exc.code
        report = asyncio.run(inspect_hml_local(
            identity=ident,
            observer=GitCheckoutReadOnlyObserver(),
            inspector=inspector,
            proxy_error=error,
            metadata_only=True,
            metadata_reader=GitHeadMetadataPeek(checkout_root=_CHECKOUT),
        ))
        print(json.dumps(asdict(report), sort_keys=True, separators=(",", ":")))
        return 0
    except Exception:
        # Never leak local usernames, paths, system errors or environmental
        # credentials to terminal/logs when the preflight fails unexpectedly.
        print(json.dumps({
            "status": "blocked", "code": "HML_PREFLIGHT_UNAVAILABLE",
            "prepare_eligible": False, "can_execute": False,
        }, sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
