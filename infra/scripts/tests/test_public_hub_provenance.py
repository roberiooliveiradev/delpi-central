"""P2.2f: offline, non-deploy contract for the Public Hub OCI build revision."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = ROOT / "plugins/public-hub/Dockerfile"
COMPOSE = ROOT / "infra/docker-compose.yml"
HML = ROOT / "infra/docker-compose.hml.yml"
HELPER = ROOT / "infra/scripts/public-hub-provenance.sh"
SCRIPTS = (
    ROOT / "infra/scripts/up-hml-sequential.sh",
    ROOT / "infra/scripts/up-prod-sequential.sh",
)


def git(root, *args):
    return subprocess.run(("git", "-C", str(root), *args), check=True,
                          text=True, capture_output=True).stdout.strip()


def run_helper(repo):
    return subprocess.run(("bash", "-c", 'source "$1"; atlas_public_hub_revision "$2"',
                           "bash", str(HELPER), str(repo)), capture_output=True,
                          text=True, check=False)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "ATLAS CI")
    git(tmp_path, "config", "user.email", "atlas-ci@example.invalid")
    base = tmp_path / "plugins/public-hub"
    base.mkdir(parents=True)
    (base / "tracked.txt").write_text("original\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "test input")
    return tmp_path


def test_revision_comes_from_exact_git_head(repo):
    got = run_helper(repo)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == git(repo, "rev-parse", "HEAD")
    assert len(got.stdout.strip()) == 40


def test_dirty_tracked_build_input_is_refused(repo):
    (repo / "plugins/public-hub/tracked.txt").write_text("modified\n", encoding="utf-8")
    got = run_helper(repo)
    assert got.returncode != 0
    assert "modificados" in got.stderr
    assert got.stdout == ""


def test_untracked_build_input_is_refused(repo):
    new = repo / "plugins/vite/generated.js"
    new.parent.mkdir(parents=True)
    new.write_text("new input", encoding="utf-8")
    got = run_helper(repo)
    assert got.returncode != 0
    assert got.stdout == ""


def test_unrelated_untracked_file_does_not_block(repo):
    (repo / "unrelated.tmp").write_text("test", encoding="utf-8")
    assert run_helper(repo).returncode == 0


def test_dockerfile_contract_stage_has_sha_gate_and_final_inheritance():
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "FROM nginx:alpine AS provenance-contract" in text
    assert "ARG SOURCE_REVISION" in text
    assert "grep -Eq '^[0-9a-f]{40}$'" in text
    assert "org.opencontainers.image.revision=\"${SOURCE_REVISION}\"" in text
    assert "org.opencontainers.image.source=\"https://github.com/roberiooliveiradev/delpi-central\"" in text
    assert "FROM provenance-contract AS production" in text
    assert "COPY --from=builder" in text


def test_compose_passes_scoped_arg_without_breaking_other_services():
    text = COMPOSE.read_text(encoding="utf-8")
    section = text.split("\n  public-hub:\n", 1)[1].split("\n  inspecoes-entrada:\n", 1)[0]
    assert "SOURCE_REVISION: ${PUBLIC_HUB_SOURCE_REVISION:-}" in section
    assert "context: ../plugins" in section
    assert "target: production" in section
    hml = HML.read_text(encoding="utf-8")
    section_hml = hml.split("\n  public-hub:\n", 1)[1].split("\n  gateway:\n", 1)[0]
    assert "service: public-hub" in section_hml
    assert "depends_on: !override {}" in section_hml
    assert "build:" not in section_hml  # Inherit prod's scoped build args.


@pytest.mark.parametrize("script", SCRIPTS)
def test_each_sequential_script_uses_guard_only_for_public_hub_build(script):
    text = script.read_text(encoding="utf-8")
    assert 'source "$SCRIPT_DIR/public-hub-provenance.sh"' in text
    assert '[[ "$BUILD" == true && "$svc" == "public-hub" ]]' in text
    assert 'PUBLIC_HUB_SOURCE_REVISION="$(atlas_public_hub_revision "$REPO_ROOT")"' in text
    assert 'export PUBLIC_HUB_SOURCE_REVISION' in text
    assert 'SOURCE_REVISION="${SOURCE_REVISION:-' in text  # Existing other apps preserved.


def test_staged_change_in_build_input_is_refused(repo):
    (repo / "plugins/public-hub/tracked.txt").write_text("staged\n", encoding="utf-8")
    git(repo, "add", "plugins/public-hub/tracked.txt")
    assert run_helper(repo).returncode != 0


def test_missing_git_repository_is_refused(tmp_path):
    got = run_helper(tmp_path)
    assert got.returncode != 0
    assert got.stdout == ""
