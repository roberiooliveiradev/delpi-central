"""P2.2h preflight is read-only, signed, pinned and fail-closed."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'public-hub-release-preflight.sh'
SHA = 'f81ddd0075de1e4ef8bb68ca58791e9c43e70759'
MANIFEST = 'sha256:' + 'a' * 64
CURRENT = 'sha256:' + 'b' * 64


@pytest.fixture()
def env(tmp_path):
    binary = tmp_path / 'bin'
    binary.mkdir()
    gh = binary / 'gh'
    gh.write_text('''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$GH_LOG"
[[ "$GH_FAIL" != 1 ]]
''')
    gh.chmod(0o755)
    docker = binary / 'docker'
    docker.write_text('''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$DOCKER_LOG"
[[ "$DOCKER_FAIL" != 1 ]] || exit 1
case "$1:$2:$4" in
  container:inspect:'{{.Image}}') echo "$ACTUAL_IMAGE" ;;
  container:inspect:'{{.State.Status}}') echo "$STATUS" ;;
  container:inspect:*com.docker.compose.service*) echo "$SERVICE" ;;
  container:inspect:*com.docker.compose.project*) echo "$PROJECT" ;;
  image:inspect:*org.opencontainers.image.revision*) echo "$CURRENT_REV" ;;
  *) exit 1 ;;
esac
''')
    docker.chmod(0o755)
    env = dict(os.environ)
    env.update({
        'PATH': f'{binary}:{env["PATH"]}',
        'GH_LOG': str(tmp_path / 'gh.log'),
        'DOCKER_LOG': str(tmp_path / 'docker.log'),
        'GH_FAIL': '0',
        'DOCKER_FAIL': '0',
        'ACTUAL_IMAGE': CURRENT,
        'STATUS': 'running',
        'SERVICE': 'public-hub',
        'PROJECT': 'infra',
        'CURRENT_REV': '03cecb7ed90946c799a66ca9b22b45beb221282e',
    })
    return env


def run(env, *args):
    return subprocess.run(['bash', str(SCRIPT), *args], env=env,
                          capture_output=True, text=True)


def plan(env, stage='prod', sha=SHA, manifest=MANIFEST, old=CURRENT):
    return run(env, '--plan', stage, sha, manifest, old)


def test_positive_prod_is_explicitly_non_executing(env):
    r = plan(env)
    assert r.returncode == 0, r.stderr
    assert '[PLAN_OK_NO_DEPLOY]' in r.stdout
    assert 'promotion=BLOCKED' in r.stdout
    assert SHA in r.stdout
    assert MANIFEST in r.stdout
    gh = Path(env['GH_LOG']).read_text()
    for flag in (
        '--signer-workflow roberiooliveiradev/delpi-central/.github/workflows/atlas-public-hub-oci.yml',
        '--source-ref refs/heads/main', '--source-digest ' + SHA,
        '--deny-self-hosted-runners', '--predicate-type https://slsa.dev/provenance/v1',
        '--cert-oidc-issuer https://token.actions.githubusercontent.com',
        '--repo roberiooliveiradev/delpi-central',
    ):
        assert flag in gh
    assert 'oci://ghcr.io/roberiooliveiradev/delpi-public-hub@' + MANIFEST in gh
    docker = Path(env['DOCKER_LOG']).read_text()
    assert 'container inspect' in docker
    assert 'image inspect' in docker
    for write in (' pull ', ' build ', ' run ', ' up ', ' stop ', ' rm ', ' tag ', ' compose ', ' exec '):
        assert write not in ' ' + docker + ' '


def test_positive_hml_uses_expected_container(env):
    env['PROJECT'] = 'delpi-hml'
    r = plan(env, stage='hml')
    assert r.returncode == 0, r.stderr
    assert 'delpi-hml-public-hub' in Path(env['DOCKER_LOG']).read_text()


@pytest.mark.parametrize('args', [
    (), ('--apply', 'prod', SHA, MANIFEST, CURRENT),
    ('--plan', 'other', SHA, MANIFEST, CURRENT),
    ('--plan', 'prod', 'f' * 39, MANIFEST, CURRENT),
    ('--plan', 'prod', 'F' * 40, MANIFEST, CURRENT),
    ('--plan', 'prod', SHA, 'sha256:' + 'a' * 63, CURRENT),
    ('--plan', 'prod', SHA, 'sha512:' + 'a' * 64, CURRENT),
    ('--plan', 'prod', SHA, MANIFEST, 'sha256:' + 'b' * 63),
])
def test_invalid_input_never_reaches_gh_or_docker(env, args):
    r = run(env, *args)
    assert r.returncode != 0
    assert '[BLOCKED]' in r.stderr
    assert not Path(env['GH_LOG']).exists()
    assert not Path(env['DOCKER_LOG']).exists()


def test_signature_failure_never_inspects_docker(env):
    env['GH_FAIL'] = '1'
    r = plan(env)
    assert r.returncode != 0
    assert 'atestado assinado nao verificado' in r.stderr
    assert not Path(env['DOCKER_LOG']).exists()


@pytest.mark.parametrize('key,value', [
    ('DOCKER_FAIL', '1'),
    ('ACTUAL_IMAGE', 'sha256:' + 'c' * 64),
    ('ACTUAL_IMAGE', 'bad'),
    ('STATUS', 'exited'),
    ('SERVICE', 'api-delpi'),
    ('PROJECT', 'delpi-hml'),
    ('PROJECT', '<no value>'),
    ('CURRENT_REV', 'unknown'),
])
def test_prod_drift_blocks(env, key, value):
    env[key] = value
    r = plan(env)
    assert r.returncode != 0
    assert '[BLOCKED]' in r.stderr


def test_hml_wrong_project_blocks(env):
    assert plan(env, stage='hml').returncode != 0


def test_script_never_has_host_mutation_apis():
    code = SCRIPT.read_text()
    for prohibited in ('docker pull ', 'docker compose ', 'docker build ', 'docker tag ',
                       'docker run ', 'docker stop ', 'docker rm ', 'docker exec ', 'ssh '):
        assert prohibited not in code
