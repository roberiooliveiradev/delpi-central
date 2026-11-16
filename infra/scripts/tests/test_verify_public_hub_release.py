"""P2.2g: read-only verifier fail-closed tests, without Docker/GitHub access."""
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "verify-public-hub-release.sh"
SHA = "a" * 40
DIGEST = "sha256:" + "b" * 64
IMAGE_ID = "sha256:" + "c" * 64


@pytest.fixture()
def fake(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text("""#!/usr/bin/env bash
printf '%s\n' "$*" >> "$GH_LOG"
[[ "$GH_FAIL" != 1 ]]
""")
    gh.chmod(0o755)
    docker = bin_dir / "docker"
    docker.write_text("""#!/usr/bin/env bash
printf '%s\n' "$*" >> "$DOCKER_LOG"
[[ "$DOCKER_FAIL" != 1 ]] || exit 1
case "$1/$4" in
 image/'{{.Id}}') echo "$IMAGE_ID" ;;
 container/'{{.Image}}') echo "$RUNNING_ID" ;;
 image/*org.opencontainers.image.revision*) echo "$REVISION" ;;
 image/*org.opencontainers.image.source*) echo "$SOURCE" ;;
 container/*com.docker.compose.service*) echo "$SERVICE" ;;
 container/*com.docker.compose.project*) echo "$PROJECT" ;;
 container/'{{.State.Status}}') echo "$STATUS" ;;
 *) exit 1 ;;
esac
""")
    docker.chmod(0o755)
    env = dict(os.environ)
    env.update({
        "PATH": f"{bin_dir}:{env['PATH']}",
        "GH_LOG": str(tmp_path / "gh.log"),
        "DOCKER_LOG": str(tmp_path / "docker.log"),
        "GH_FAIL": "0",
        "DOCKER_FAIL": "0",
        "IMAGE_ID": IMAGE_ID,
        "RUNNING_ID": IMAGE_ID,
        "REVISION": SHA,
        "SOURCE": "https://github.com/roberiooliveiradev/delpi-central",
        "SERVICE": "public-hub",
        "PROJECT": "delpi-hml",
        "STATUS": "running",
    })
    return env


def verify(env, sha=SHA, digest=DIGEST, target="prod"):
    return subprocess.run(["bash", str(SCRIPT), sha, digest, target],
                          env=env, text=True, capture_output=True)


def test_positive_prod_and_signature_requirements(fake):
    result = verify(fake)
    assert result.returncode == 0, result.stderr
    gh = Path(fake["GH_LOG"]).read_text()
    for value in ("--repo roberiooliveiradev/delpi-central",
                  "--source-digest " + SHA,
                  "--source-ref refs/heads/main",
                  "--signer-workflow roberiooliveiradev/delpi-central/.github/workflows/atlas-public-hub-oci.yml",
                  "--predicate-type https://slsa.dev/provenance/v1",
                  "--deny-self-hosted-runners"):
        assert value in gh
    assert "oci://ghcr.io/roberiooliveiradev/delpi-public-hub@" + DIGEST in gh


def test_positive_hml(fake):
    assert verify(fake, target="hml").returncode == 0
    assert "delpi-hml-public-hub" in Path(fake["DOCKER_LOG"]).read_text()


@pytest.mark.parametrize("sha,digest,target", [
    ("a" * 39, DIGEST, "prod"),
    ("A" * 40, DIGEST, "prod"),
    (SHA, "sha256:" + "b" * 63, "prod"),
    (SHA, "sha512:" + "b" * 64, "prod"),
    (SHA, DIGEST, "other"),
    (SHA, DIGEST, "../../../etc"),
])
def test_invalid_args_block_without_external_calls(fake, sha, digest, target):
    result = verify(fake, sha, digest, target)
    assert result.returncode != 0
    assert not Path(fake["GH_LOG"]).exists()
    assert not Path(fake["DOCKER_LOG"]).exists()


def test_invalid_signature_blocks_before_runtime(fake):
    fake["GH_FAIL"] = "1"
    assert verify(fake).returncode != 0
    assert not Path(fake["DOCKER_LOG"]).exists()


@pytest.mark.parametrize("field,value", [
    ("DOCKER_FAIL", "1"),
    ("IMAGE_ID", "bad"),
    ("RUNNING_ID", "sha256:" + "d" * 64),
    ("REVISION", "d" * 40),
    ("SOURCE", "https://github.com/bad/repo"),
    ("SERVICE", "other"),
    ("STATUS", "exited"),
])
def test_drift_is_denied(fake, field, value):
    fake[field] = value
    assert verify(fake).returncode != 0


def test_bad_hml_project_denied(fake):
    fake["PROJECT"] = "delpi-prod"
    assert verify(fake, target="hml").returncode != 0


def test_read_only_contract():
    contents = SCRIPT.read_text()
    assert "docker pull " not in contents
    assert "docker build " not in contents
    assert "docker compose " not in contents
    assert "git pull " not in contents
