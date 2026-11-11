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

    assert "OnCalendar=hourly" in timer
    assert "Persistent=true" in timer
    assert "RandomizedDelaySec=5m" in timer
    assert "WantedBy=timers.target" in timer
    assert "# WantedBy=timers.target" not in timer

    assert "User=delpi-collector" in service
    assert "EnvironmentFile=/etc/delpi/it-portal-linux-collector.env" in service
    assert "EnvironmentFile=-/etc/delpi" not in service
    assert "/opt/delpi/it-portal-collector/bin/run-collector submit" in service
    assert "flock -n" in service
    assert "TimeoutStartSec=120" in service
    assert "NoNewPrivileges=true" in service

    # O enable aparece só no texto de ajuda final — nunca no corpo executável.
    installer_body = installer.split("cat <<EOF", 1)[0]
    assert "systemctl enable" not in installer_body
    assert "usermod" not in installer_body
    assert "gpasswd" not in installer_body
    assert "docker" in installer  # documenta ausência / aviso, sem conceder
    assert "arquivo de ambiente obrigatório ausente" in wrapper
    assert (deploy / "it-portal-linux-collector.env.example").is_file()
    assert (deploy / "requirements-collector.txt").is_file()
