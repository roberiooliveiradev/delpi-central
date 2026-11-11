"""Parsers e artefatos systemd do coletor Linux — positive / sibling / negative."""

from pathlib import Path

from collectors.linux_host.parsing import (
    filter_host_nics,
    is_host_nic,
    memory_summary_from_meminfo,
    os_summary_from_release,
    parse_df_posix,
    parse_meminfo_kb,
    parse_os_release,
    parse_systemctl_show,
)


def test_parse_os_release_and_meminfo():
    release = parse_os_release(
        'NAME="Ubuntu"\nVERSION_ID="24.04"\nPRETTY_NAME="Ubuntu 24.04.1 LTS"\n'
    )
    os_info = os_summary_from_release(release, kernel="6.8.0", arch="x86_64")
    assert os_info["name"] == "Ubuntu"
    assert os_info["version"] == "24.04"

    mem = parse_meminfo_kb("MemTotal:       16384000 kB\nMemAvailable:    8192000 kB\n")
    summary = memory_summary_from_meminfo(mem)
    assert summary["total_bytes"] == 16384000 * 1024
    assert summary["available_bytes"] == 8192000 * 1024


def test_filter_host_nics_drops_docker_bridges():
    nics = filter_host_nics(
        [
            {"name": "eth0", "addresses": ["10.0.0.1/24"], "state": "up"},
            {"name": "docker0", "addresses": ["172.17.0.1/16"], "state": "up"},
            {"name": "br-deadbeef", "addresses": [], "state": "up"},
            {"name": "veth123", "addresses": [], "state": "up"},
            {"name": "wlan0", "addresses": ["192.168.0.10/24"], "state": "up"},
        ]
    )
    assert [n["name"] for n in nics] == ["eth0", "wlan0"]
    assert is_host_nic("lo") is True
    assert is_host_nic("cni0") is False


def test_parse_df_and_systemctl():
    df = parse_df_posix(
        "Filesystem     1024-blocks      Used Available Capacity Mounted on\n"
        "/dev/sda1      100000000  40000000  60000000      40% /\n"
        "tmpfs               1000       10       990       1% /run\n"
    )
    assert df[0]["mount_point"] == "/"
    assert df[0]["used_percent"] == 40.0

    show = parse_systemctl_show(
        "ActiveState=active\nSubState=running\nUnitFileState=enabled\n"
    )
    assert show["active_state"] == "active"
    assert show["unit_file_state"] == "enabled"


def test_systemd_units_are_ready_for_hourly_enable_without_auto_start():
    deploy = Path(__file__).resolve().parents[1] / "collectors" / "linux_host" / "deploy"
    service = (deploy / "it-portal-linux-collector.service").read_text(encoding="utf-8")
    timer = (deploy / "it-portal-linux-collector.timer").read_text(encoding="utf-8")
    installer = (deploy / "install-it-portal-linux-collector.sh").read_text(encoding="utf-8")
    wrapper = (deploy / "run-collector.sh").read_text(encoding="utf-8")
    verify = (deploy / "verify-collector-permissions.sh").read_text(encoding="utf-8")
    vendor_pyproject = (deploy / "vendor-delpi-auth-pyproject.toml").read_text(encoding="utf-8")
    requirements = (deploy / "requirements-collector.txt").read_text(encoding="utf-8")

    assert "OnCalendar=hourly" in timer
    assert "Persistent=true" in timer
    assert "RandomizedDelaySec=5m" in timer
    assert "WantedBy=timers.target" in timer
    assert "# WantedBy=timers.target" not in timer
    # Timer não puxa o oneshot na ativação — só o calendário dispara o serviço.
    assert "Requires=it-portal-linux-collector.service" not in timer

    assert "User=delpi-collector" in service
    assert "EnvironmentFile=/etc/delpi/it-portal-linux-collector.env" in service
    assert "EnvironmentFile=-/etc/delpi" not in service
    assert "/opt/delpi/it-portal-collector/bin/run-collector submit" in service
    assert "flock -n" in service
    assert "TimeoutStartSec=120" in service
    assert "NoNewPrivileges=true" in service
    assert "ReadWritePaths=/var/lib/it-portal-collector" in service
    assert "ReadOnlyPaths=/opt/delpi/it-portal-collector" in service
    assert "PYTHONDONTWRITEBYTECODE=1" in service

    # O enable aparece só no texto de ajuda final — nunca no corpo executável.
    installer_body = installer.split("cat <<EOF", 1)[0]
    assert "systemctl enable" not in installer_body
    assert "usermod" not in installer_body
    assert "gpasswd" not in installer_body
    assert "docker" in installer  # documenta ausência / aviso, sem conceder
    assert "harden_install_tree" in installer_body
    assert installer_body.count("harden_install_tree") >= 4  # antes do sync, pós-sync, pós-venv, pós-pip
    assert 'chown -R root:root "${INSTALL_ROOT}"' in installer_body
    assert f'chown -R "${{SERVICE_USER}}"' not in installer_body
    assert "chown -R delpi-collector" not in installer_body
    assert "pip install -e" not in installer_body
    assert "install --no-deps" in installer_body
    assert "shared/delpi_auth" in installer_body
    assert "verify-collector-permissions" in installer_body
    # Idempotência: reinstall não sobrescreve env existente; reaplica modos.
    assert "preservando" in installer_body and "não sobrescrito" in installer_body
    assert "harden_state_and_env" in installer_body
    assert "name = \"delpi-auth\"" in vendor_pyproject
    assert "não-editable" in requirements or "NÃO-EDITABLE" in requirements
    assert "arquivo de ambiente obrigatório ausente" in wrapper
    assert "PYTHONDONTWRITEBYTECODE=1" in wrapper
    assert "não escreve em ${INSTALL_ROOT}" in verify or "não escreve em" in verify
    assert (deploy / "it-portal-linux-collector.env.example").is_file()
    assert (deploy / "requirements-collector.txt").is_file()
    assert (deploy / "verify-collector-permissions.sh").is_file()
    assert (deploy / "vendor-delpi-auth-pyproject.toml").is_file()


def test_collector_permission_model_negative_and_positive(tmp_path: Path):
    """Simula ownership: árvore de código sem escrita; state gravável."""
    install_root = tmp_path / "opt" / "it-portal-collector"
    state_dir = tmp_path / "var" / "it-portal-collector"
    (install_root / "bin").mkdir(parents=True)
    (install_root / "collectors" / "linux_host").mkdir(parents=True)
    (install_root / "vendor" / "shared").mkdir(parents=True)
    (install_root / "venv" / "bin").mkdir(parents=True)
    state_dir.mkdir(parents=True)

    wrapper = install_root / "bin" / "run-collector"
    code = install_root / "collectors" / "linux_host" / "submit.py"
    vendor = install_root / "vendor" / "shared" / "pyproject.toml"
    venv_py = install_root / "venv" / "bin" / "python"
    for path, content in (
        (wrapper, "#!/bin/sh\n"),
        (code, "print('ok')\n"),
        (vendor, "[project]\nname='delpi-auth'\n"),
        (venv_py, "#!/bin/sh\n"),
    ):
        path.write_text(content, encoding="utf-8")

    # Remove escrita de toda a árvore de instalação (modelo root-owned endurecido).
    for path in sorted(install_root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    install_root.chmod(0o555)
    state_dir.chmod(0o750)

    probe = install_root / ".write-probe"
    try:
        probe.write_text("x", encoding="utf-8")
        raised = False
    except OSError:
        raised = True
    assert raised, "código/install_root não deve ser gravável"

    for path in (wrapper, code, vendor, venv_py):
        try:
            with path.open("a", encoding="utf-8") as handle:
                handle.write("x")
            writable = True
        except OSError:
            writable = False
        assert not writable, f"{path} não deve ser modificável"

    state_probe = state_dir / ".write-probe"
    state_probe.write_text("ok", encoding="utf-8")
    assert state_probe.read_text(encoding="utf-8") == "ok"
    state_probe.unlink()
