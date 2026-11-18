"""Fail-closed review tests for ATLAS's intentionally non-runnable units.

Only checked-in '.review' source strings are read; systemd and the real host
are never contacted, and no Docker/Keycloak/DB/production process is changed.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest

from linux_ops_mcp import atlas_hml_supervisor_blueprint_review as review


@pytest.fixture
def files():
    return review.load_repository_blueprint_sources()


def test_checked_in_supervisor_blueprint_is_only_a_blocked_draft(files):
    report = review.review_blueprint_sources(files)
    assert report.status == "blocked"
    assert report.scope == "hml/public-hub"
    assert report.files_reviewed == 8
    for name, value in asdict(report).items():
        if name.endswith("_attested") or name.endswith("_approved") or name in (
            "systemd_units_installed", "prepare_eligible", "can_execute",
        ):
            assert value is False, name
    assert "ROOT_PRODUCER_DOCKER_PRIVILEGE_UNREVIEWED" in report.blocks
    assert "INDEPENDENT_SECURITY_REVIEW_REQUIRED" in report.blocks
    assert "PREPARE_DISABLED" in report.blocks
    assert "ACT_DISABLED" in report.blocks
    assert all(path.endswith(".review") for path in files)
    assert "[Socket]" not in files["atlas-hml-local-signer.socket.review"]
    assert "[Install]" not in files["atlas-hml-local-signer.socket.review"]
    assert "ROOT_PREBOUND_SIGNER_SOCKET_REJECTED" in report.blocks


@pytest.mark.parametrize("file_name,old,new", [
    ("atlas-hml-snapshot-producer.service.review",
     "ExecStart=/usr/bin/false", "ExecStart=/usr/bin/python3 /opt/atlas/producer.py"),
    ("atlas-hml-snapshot-presenter.service.review",
     "ExecStart=/usr/bin/false", "ExecStart=/usr/bin/python3 -m linux_ops_mcp.server"),
    ("atlas-hml-snapshot-producer.service.review",
     "User=root", "User=atlas-hml"),
    ("atlas-hml-snapshot-presenter.service.review",
     "User=atlas-hml", "User=root"),
    ("atlas-hml-snapshot-presenter.service.review",
     "Group=atlas-hml", "Group=docker"),
    ("atlas-hml-nonroot-bridge.service.review",
     "User=atlas-hml-bridge", "User=root"),
    ("atlas-hml-nonroot-bridge.service.review",
     "SupplementaryGroups=atlas-hml", "SupplementaryGroups=atlas-hml docker"),
    ("atlas-hml-nonroot-bridge.service.review",
     "ExecStart=/usr/bin/false", "ExecStart=/usr/bin/python3 /opt/atlas/bridge.py"),
    ("atlas-hml-local-signer.socket.review",
     "Description=ATLAS HML SIGNER SOCKET ACTIVATION SUPERSEDED REVIEW ONLY",
     "Description=ATLAS HML LOCAL SIGNER SOCKET REVIEW ONLY"),
    ("atlas-hml-local-signer.service.review",
     "ReadWritePaths=/run/atlas-hml-signer-socket /var/lib/atlas-hml-signer-state",
     "ReadWritePaths=/run/docker.sock"),
    ("atlas-hml-local-signer.service.review",
     "SupplementaryGroups=", "SupplementaryGroups=docker"),
    ("atlas-hml-snapshot-presenter.service.review",
     "SupplementaryGroups=", "SupplementaryGroups=docker"),
    ("atlas-hml-snapshot-presenter.service.review",
     "NoNewPrivileges=yes", "NoNewPrivileges=no"),
    ("atlas-hml-snapshot-producer.service.review",
     "NoNewPrivileges=yes", "NoNewPrivileges=no"),
    ("atlas-hml-snapshot-presenter.service.review",
     "CapabilityBoundingSet=", "CapabilityBoundingSet=CAP_SYS_ADMIN"),
    ("atlas-hml-snapshot-presenter.service.review",
     "AmbientCapabilities=", "AmbientCapabilities=CAP_SYS_ADMIN"),
    ("atlas-hml-snapshot-presenter.service.review",
     "RestrictAddressFamilies=AF_UNIX",
     "RestrictAddressFamilies=AF_UNIX AF_INET"),
    ("atlas-hml-snapshot-presenter.service.review",
     "InaccessiblePaths=/run/docker.sock /var/run/docker.sock",
     "InaccessiblePaths="),
    ("atlas-hml-snapshot-presenter.service.review",
     "ReadOnlyPaths=/run/atlas-hml-readonly",
     "ReadWritePaths=/run/atlas-hml-readonly"),
    ("atlas-hml-snapshot-producer.service.review",
     "ProtectSystem=strict", "ProtectSystem=no"),
    ("atlas-hml-snapshot-presenter.socket.review",
     "SocketUser=root", "SocketUser=atlas-hml"),
    ("atlas-hml-snapshot-presenter.socket.review",
     "SocketGroup=atlas-hml", "SocketGroup=docker"),
    ("atlas-hml-snapshot-presenter.socket.review",
     "SocketMode=0660", "SocketMode=0666"),
    ("atlas-hml-snapshot-presenter.socket.review",
     "DirectoryMode=0750", "DirectoryMode=0777"),
    ("atlas-hml-snapshot-presenter.socket.review",
     "ListenStream=/run/atlas-hml-readonly/inspect.sock",
     "ListenStream=/run/docker.sock"),
    ("atlas-hml-snapshot-presenter.socket.review",
     "Accept=no", "Accept=yes"),
    ("atlas-hml-snapshot-producer.timer.review",
     "Persistent=no", "Persistent=yes"),
    ("atlas-hml-snapshot-producer.timer.review",
     "OnUnitActiveSec=30s", "OnUnitActiveSec=1ms"),
    ("atlas-hml-snapshot-producer.timer.review",
     "Unit=atlas-hml-snapshot-producer.service",
     "Unit=delpi-public-hub.service"),
])
def test_any_unsafe_unit_drift_is_rejected(files, file_name, old, new):
    assert old in files[file_name], (file_name, old)
    mutated = {**files, file_name: files[file_name].replace(old, new, 1)}
    with pytest.raises(
        review.HMLSupervisorBlueprintError, match="HML_BLUEPRINT_POLICY_DRIFT",
    ):
        review.review_blueprint_sources(mutated)


@pytest.mark.parametrize("new_line", [
    "ExecStartPre=/usr/bin/sh -c 'touch /tmp/unsafe'",
    "Environment=DOCKER_HOST=tcp://0.0.0.0:2375",
    "ReadWritePaths=/var/run/docker.sock",
    "BindPaths=/run/docker.sock",
])
def test_hidden_or_added_privileged_directives_are_denied(files, new_line):
    file_name = "atlas-hml-snapshot-presenter.service.review"
    source = files[file_name] + new_line + "\n"
    with pytest.raises(
        review.HMLSupervisorBlueprintError, match="HML_BLUEPRINT_POLICY_DRIFT",
    ):
        review.review_blueprint_sources({**files, file_name: source})


def test_legacy_signer_socket_cannot_regain_a_listener(files):
    name = "atlas-hml-local-signer.socket.review"
    changed = files[name] + (
        "\n[Socket]\nListenStream=/run/atlas-hml-signer/sign.sock\n"
        "SocketUser=root\nSocketGroup=atlas-hml-bridge\nSocketMode=0660\n"
    )
    with pytest.raises(review.HMLSupervisorBlueprintError,
                       match="HML_BLUEPRINT_POLICY_DRIFT"):
        review.review_blueprint_sources({**files, name: changed})


def test_no_service_template_may_gain_an_install_section(files):
    name = "atlas-hml-snapshot-producer.service.review"
    with pytest.raises(
        review.HMLSupervisorBlueprintError, match="HML_BLUEPRINT_POLICY_DRIFT",
    ):
        review.review_blueprint_sources({
            **files, name: files[name] + "\n[Install]\nWantedBy=multi-user.target\n",
        })


def test_runtime_activation_guard_cannot_be_removed(files):
    for name, source in files.items():
        if name.endswith("tmpfiles.review"):
            continue
        changed = source
        for sentinel in (
            "ConditionPathExists=/run/atlas-hml-readonly/REVIEW-ONLY-NEVER-CREATE",
            "ConditionPathExists=/run/atlas-hml-signer/REVIEW-ONLY-NEVER-CREATE",
        ):
            changed = changed.replace(
                sentinel, "ConditionPathExists=/etc/os-release",
            )
        with pytest.raises(
            review.HMLSupervisorBlueprintError, match="HML_BLUEPRINT_POLICY_DRIFT",
        ):
            review.review_blueprint_sources({**files, name: changed})
        changed = source.replace("RefuseManualStart=yes", "RefuseManualStart=no")
        with pytest.raises(
            review.HMLSupervisorBlueprintError, match="HML_BLUEPRINT_POLICY_DRIFT",
        ):
            review.review_blueprint_sources({**files, name: changed})


@pytest.mark.parametrize("replacement", [
    "d /run/atlas-hml-readonly 0777 root atlas-hml -",
    "d /run/atlas-hml-readonly 0750 root docker -",
    "d /run/atlas-hml-readonly 0750 atlas-hml atlas-hml -",
    "d /run/docker.sock 0660 root atlas-hml -",
])
def test_runtime_parent_dir_policy_never_weakens(files, replacement):
    name = "atlas-hml-runtime-dir.tmpfiles.review"
    source = files[name].replace(
        "d /run/atlas-hml-readonly 0750 root atlas-hml -", replacement,
    )
    with pytest.raises(
        review.HMLSupervisorBlueprintError,
        match="HML_BLUEPRINT_TMPFILES_UNSAFE",
    ):
        review.review_blueprint_sources({**files, name: source})


def test_missing_extra_or_renamed_runtime_files_rejected(files):
    for mutated in (
        {k:v for k,v in files.items() if "producer.timer" not in k},
        {**files, "atlas-hml-live.service": files[
            "atlas-hml-snapshot-presenter.service.review"]},
    ):
        with pytest.raises(
            review.HMLSupervisorBlueprintError, match="HML_BLUEPRINT_SET_INVALID",
        ):
            review.review_blueprint_sources(mutated)


def test_malformed_ini_and_duplicate_directives_fail_closed(files):
    name = "atlas-hml-snapshot-presenter.service.review"
    source = files[name]
    for bad in (source + "\n[Unit]\n", source + "\n[Service]\nUser=root\n",
                source + "\nExecStart=/usr/bin/true\n"):
        with pytest.raises(review.HMLSupervisorBlueprintError):
            review.review_blueprint_sources({**files, name: bad})


def test_source_type_limit_and_private_payload_do_not_leak(files):
    name = "atlas-hml-snapshot-presenter.socket.review"
    for bad in (b"not a string", "x" * 8193, "secret\x00"):
        with pytest.raises(
            review.HMLSupervisorBlueprintError, match="HML_BLUEPRINT_SOURCE_INVALID",
        ):
            review.review_blueprint_sources({**files, name: bad})


def test_no_runtime_entrypoint_available_in_static_review_module():
    for name in (
        "main", "serve", "deploy", "start", "enable", "create_mcp_server",
        "install_systemd_units", "write_host_unit",
    ):
        assert not hasattr(review, name)
