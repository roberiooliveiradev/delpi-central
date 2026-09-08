#!/usr/bin/env python3
"""Gates transversais incrementais da plataforma Minha DELPI.

O auditor é diff-aware: dívida existente não falha o CI; apenas regressões novas
ou mutações proibidas no diff são bloqueadas.

Regras:
- IMMUTABLE_MIGRATION_MUTATION: migration SQL V*__*.sql já versionada não pode ser
  modificada, renomeada ou removida; evolução usa nova migration.
- MFE_GLOBAL_CSS: MFE não pode introduzir seletores CSS globais no documento host.
- MFE_PLUGIN_UI_OVERRIDE: MFE não pode estilizar classes .delpi-ui-*; o CSS do kit
  pertence a plugins/plugin-ui.
- MFE_OWN_API_BYPASS: se plugins/<app> possui <app>-api no monorepo, seu código de
  frontend não pode introduzir chamada direta a /apps/api-delpi.
- JWT_VERIFY_DISABLED: código de produção não pode desabilitar ou condicionar
  verificação de assinatura/audience/issuer explicitamente.
- JWT_VALIDATOR_DUPLICATION: nova API não pode criar validação JWT paralela com
  jwt.decode; usar shared/delpi_auth.
- AUTHZ_PRIMITIVE_DUPLICATION: nova API não pode redefinir primitives genéricas
  require_auth/require_permission/... fora do shared/Core canônico.

Uso:
  python scripts/ci/audit_platform_guardrails.py --check --base <sha>
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIGRATION_RE = re.compile(r"(?:^|/)migrations/(?:.*/)?V\d+__[^/]+\.sql$", re.IGNORECASE)
GLOBAL_CSS_RE = re.compile(r"^\s*(?::root|body|html|#root|\*)\s*\{")
PLUGIN_UI_CLASS_RE = re.compile(r"\.delpi-ui-[A-Za-z0-9_-]+")
API_DELPI_GATEWAY_RE = re.compile(r"(?:^|[\"'`])/?apps/api-delpi(?:/|[\"'`])", re.IGNORECASE)
JWT_VERIFY_DISABLED_RE = re.compile(
    r"(?:verify_signature|verify_aud|verify_iss|verify_exp|verify_nbf|verify_iat)"
    r"[\"']?\s*[=:]\s*(?:False|false|0)",
    re.IGNORECASE,
)
JWT_VERIFY_CONDITIONAL_RE = re.compile(
    r"[\"'](?:verify_aud|verify_iss|verify_signature)[\"']\s*:\s*bool\s*\(",
    re.IGNORECASE,
)
JWT_DIRECT_DECODE_RE = re.compile(r"\bjwt\.decode\s*\(")
AUTHZ_PRIMITIVE_RE = re.compile(
    r"^\s*(?:async\s+)?def\s+"
    r"(require_auth|require_permission|require_any_permission|require_all_permissions|require_superadmin)\s*\("
)

MFE_SHARED_EXCLUSIONS = {"plugin-ui", "tv-dashboard-presentation", "vite", "docker"}
PRODUCTION_CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}
MFE_CODE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}
SKIP_SECURITY_PARTS = ("/tests/", "/test/", "/fixtures/", "/docs/", "/.cursor/")
AUTH_CANONICAL_PREFIXES = ("shared/delpi_auth/", "core-api/")


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    line: int
    message: str

    def format(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"[{self.rule}] {where} — {self.message}"


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} falhou")
    return result.stdout


def resolve_base(explicit: str | None) -> str:
    candidate = (explicit or os.getenv("PLATFORM_GUARDRAILS_BASE_SHA") or "").strip()
    if not candidate or set(candidate) == {"0"}:
        candidate = git("rev-parse", "HEAD^", check=False).strip()
    if not candidate:
        raise RuntimeError("não foi possível resolver commit base; informe --base")
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{candidate}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"commit base não disponível no checkout: {candidate}")
    return candidate


def changed_paths(base: str) -> list[tuple[str, list[str]]]:
    """Retorna status e paths envolvidos (rename possui antigo + novo)."""
    raw = git("diff", "--name-status", "-M", f"{base}..HEAD", "--", ".")
    rows: list[tuple[str, list[str]]] = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        rows.append((parts[0], parts[1:]))
    return rows


def added_lines(base: str) -> dict[str, dict[int, str]]:
    diff = git("diff", "--unified=0", "--no-color", f"{base}..HEAD", "--", ".")
    files: dict[str, dict[int, str]] = {}
    current: str | None = None
    new_line: int | None = None
    hunk_re = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            current = raw[6:]
            files.setdefault(current, {})
            new_line = None
            continue
        if raw.startswith("+++ /dev/null"):
            current = None
            new_line = None
            continue
        if raw.startswith("@@"):
            match = hunk_re.search(raw)
            new_line = int(match.group(1)) if match else None
            continue
        if current is None or new_line is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            files[current][new_line] = raw[1:]
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        else:
            new_line += 1

    return {path: lines for path, lines in files.items() if lines}


def is_versioned_migration(path: str) -> bool:
    return bool(MIGRATION_RE.search(path.replace("\\", "/")))


def scan_migration_mutations(base: str) -> list[Violation]:
    findings: list[Violation] = []
    for status, paths in changed_paths(base):
        kind = status[:1]
        if kind == "A":
            continue
        migration_paths = [path for path in paths if is_versioned_migration(path)]
        if not migration_paths:
            continue
        if kind in {"M", "D", "R", "T"}:
            findings.append(
                Violation(
                    "IMMUTABLE_MIGRATION_MUTATION",
                    migration_paths[0],
                    0,
                    "migration versionada foi modificada/renomeada/removida; crie uma nova VNNN__*.sql",
                )
            )
    return findings


def plugin_name_from_path(path: str) -> str | None:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    if len(parts) < 3 or parts[0] != "plugins":
        return None
    plugin = parts[1]
    return None if plugin in MFE_SHARED_EXCLUSIONS else plugin


def is_mfe_css(path: str) -> bool:
    return plugin_name_from_path(path) is not None and path.lower().endswith(".css")


def scan_mfe_css(path: str, lines: dict[int, str]) -> list[Violation]:
    if not is_mfe_css(path):
        return []
    findings: list[Violation] = []
    for line_no, line in lines.items():
        stripped = line.strip()
        if not stripped or stripped.startswith("/*") or stripped.startswith("//"):
            continue
        if GLOBAL_CSS_RE.search(line):
            findings.append(
                Violation(
                    "MFE_GLOBAL_CSS",
                    path,
                    line_no,
                    f"seletor global introduzido no MFE: {stripped}",
                )
            )
        if PLUGIN_UI_CLASS_RE.search(line):
            findings.append(
                Violation(
                    "MFE_PLUGIN_UI_OVERRIDE",
                    path,
                    line_no,
                    "classe .delpi-ui-* estilizada no MFE; corrija o componente em plugins/plugin-ui ou use tokens",
                )
            )
    return findings


def mfe_has_own_api(path: str) -> bool:
    plugin = plugin_name_from_path(path)
    return bool(plugin and (ROOT / f"{plugin}-api").is_dir())


def scan_mfe_own_api_bypass(path: str, lines: dict[int, str]) -> list[Violation]:
    plugin = plugin_name_from_path(path)
    if (
        not plugin
        or Path(path).suffix.lower() not in MFE_CODE_EXTENSIONS
        or not mfe_has_own_api(path)
    ):
        return []

    findings: list[Violation] = []
    for line_no, line in lines.items():
        if API_DELPI_GATEWAY_RE.search(line):
            findings.append(
                Violation(
                    "MFE_OWN_API_BYPASS",
                    path,
                    line_no,
                    f"MFE {plugin!r} possui {plugin}-api e não pode chamar /apps/api-delpi diretamente; use sua API/BFF",
                )
            )
    return findings


def is_production_code(path: str) -> bool:
    normalized = "/" + path.replace("\\", "/").lstrip("/")
    if Path(path).suffix.lower() not in PRODUCTION_CODE_EXTENSIONS:
        return False
    return not any(part in normalized for part in SKIP_SECURITY_PARTS)


def is_api_python(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    if not parts or not normalized.endswith(".py"):
        return False
    root = parts[0]
    return root in {"api-delpi", "core-api"} or root.endswith("-api")


def is_auth_canonical_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(AUTH_CANONICAL_PREFIXES)


def scan_jwt_verify_disabled(path: str, lines: dict[int, str]) -> list[Violation]:
    if not is_production_code(path):
        return []
    findings: list[Violation] = []
    for line_no, line in lines.items():
        if JWT_VERIFY_DISABLED_RE.search(line) or JWT_VERIFY_CONDITIONAL_RE.search(line):
            findings.append(
                Violation(
                    "JWT_VERIFY_DISABLED",
                    path,
                    line_no,
                    "verificação de assinatura/audience/issuer JWT foi desabilitada ou condicionada por configuração opcional",
                )
            )
    return findings


def scan_jwt_validator_duplication(path: str, lines: dict[int, str]) -> list[Violation]:
    if not is_api_python(path) or is_auth_canonical_path(path) or path.startswith("core-api/"):
        return []
    findings: list[Violation] = []
    for line_no, line in lines.items():
        if JWT_DIRECT_DECODE_RE.search(line):
            findings.append(
                Violation(
                    "JWT_VALIDATOR_DUPLICATION",
                    path,
                    line_no,
                    "nova validação JWT local detectada; use/adapte shared/delpi_auth em vez de manter validator paralelo",
                )
            )
    return findings


def scan_authz_primitive_duplication(path: str, lines: dict[int, str]) -> list[Violation]:
    if not is_api_python(path) or is_auth_canonical_path(path) or path.startswith("core-api/"):
        return []
    findings: list[Violation] = []
    for line_no, line in lines.items():
        match = AUTHZ_PRIMITIVE_RE.search(line)
        if match:
            findings.append(
                Violation(
                    "AUTHZ_PRIMITIVE_DUPLICATION",
                    path,
                    line_no,
                    f"primitive genérica {match.group(1)} redefinida localmente; reutilize shared/delpi_auth ou adapte sem duplicar política",
                )
            )
    return findings


def collect(base: str) -> list[Violation]:
    findings = scan_migration_mutations(base)
    for path, lines in added_lines(base).items():
        findings.extend(scan_mfe_css(path, lines))
        findings.extend(scan_mfe_own_api_bypass(path, lines))
        findings.extend(scan_jwt_verify_disabled(path, lines))
        findings.extend(scan_jwt_validator_duplication(path, lines))
        findings.extend(scan_authz_primitive_duplication(path, lines))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        base = resolve_base(args.base)
        findings = collect(base)
    except RuntimeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2

    print("Platform guardrails")
    print(f"- base: {base}")
    print(f"- findings: {len(findings)}")
    for finding in findings:
        print(f"- {finding.format()}")

    if findings and args.check:
        print("FALHOU: novas regressões transversais detectadas", file=sys.stderr)
        return 1

    print("OK: nenhuma nova regressão transversal detectada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
