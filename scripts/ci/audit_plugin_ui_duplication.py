#!/usr/bin/env python3
"""Detecta duplicação local de componentes @delpi/plugin-ui e integração incompleta.

Uso:
  python3 scripts/ci/audit_plugin_ui_duplication.py
  python3 scripts/ci/audit_plugin_ui_duplication.py --check
  python3 scripts/ci/audit_plugin_ui_duplication.py --check --strict

Exit 0 = OK; exit 1 = violações bloqueantes (ou qualquer duplicata em --strict).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS_DIR = ROOT / "plugins"
MANIFEST_PATH = PLUGINS_DIR / "shared-libraries.manifest.json"

# Componentes cujo arquivo local deve ser wrapper fino (create* / @delpi/plugin-ui).
DUPLICATE_COMPONENT_BASENAMES = frozenset(
    {
        "HelpTooltip.tsx",
        "KpiCard.tsx",
        "ChartCard.tsx",
        "LoadingActivityCard.tsx",
        "MultiSelectField.tsx",
        "Pagination.tsx",
        "PaginationPageJump.tsx",
        "TablePageSizeSelect.tsx",
        "DataTable.tsx",
        "DataTableSection.tsx",
        "PageHeader.tsx",
        "DetailFieldGrid.tsx",
        "EditableSectionCard.tsx",
        "EmptyState.tsx",
        "LoadingState.tsx",
        "ConfirmDialog.tsx",
        "FileDropzone.tsx",
    }
)

# Implementação local legítima (domínio ou design system) — não falha em --strict.
LOCAL_IMPLEMENTATION_ALLOWLIST: dict[tuple[str, str], str] = {
    ("maintenance", "DataTableSection.tsx"): "serverTable + cabeçalho dm-section-header",
}

# Plugins fora do escopo de migração plugin-ui.
EXCLUDED_PLUGINS = frozenset(
    {
        "plugin-ui",
        "portal",
        "minha-delpi-chat",
        "strategic-indicators",
        "api-delpi-console",
        "customer-experience",
        "cultura-delpi",
        "public-hub",
        "central-agendamento",
        "quality-labels",
        "tv-dashboard-presentation",
    }
)

VITE_CONFIG_NAMES = ("vite.config.ts", "vite.config.js", "vite.config.mts")
ENTRY_FILES = ("src/main.tsx", "src/bootstrap.tsx")

WRAPPER_MARKERS = (
    "@delpi/plugin-ui",
    "plugin-ui/src/",
    "../plugin-ui/",
    "createDashboard",
    "createFilterBarShell",
    "createSimpleKpiCard",
    "createPanelCard",
    "createContentCard",
    "createMetricKpiCard",
    "createTablePaginationNav",
    "createCompactPagination",
    "createInfoGrid",
    "createModalShell",
    "createConfirmModalPanel",
    "createInfoStatePanel",
    "createStateBoxPanel",
)


@dataclass(frozen=True)
class Finding:
    level: str  # error | warning
    plugin: str
    message: str


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def library_directories(manifest: dict) -> set[str]:
    return {entry["directory"] for entry in manifest.get("libraries", [])}


def plugin_candidates(manifest: dict) -> list[Path]:
    lib_dirs = library_directories(manifest)
    plugins: list[Path] = []
    for path in sorted(PLUGINS_DIR.iterdir()):
        if not path.is_dir() or path.name in lib_dirs or path.name in EXCLUDED_PLUGINS:
            continue
        if (path / "package.json").exists():
            plugins.append(path)
    return plugins


def _component_stem(basename: str) -> str:
    return basename.removesuffix(".tsx").removesuffix(".ts")


def has_local_hook_implementation(content: str, basename: str) -> bool:
    """Detecta implementação React completa (hooks) exportada com o nome do arquivo."""
    stem = _component_stem(basename)
    export_patterns = (
        rf"export\s+function\s+{re.escape(stem)}\s*\(",
        rf"export\s+const\s+{re.escape(stem)}\s*=",
    )
    if not any(re.search(pattern, content) for pattern in export_patterns):
        return False
    if re.search(rf"create\w*{re.escape(stem)}", content, re.IGNORECASE):
        return False
    if "createDashboard" in content:
        return False
    return bool(re.search(r"\buseState\s*\(|\buseEffect\s*\(", content))


def is_thin_wrapper_content(content: str, *, basename: str = "") -> bool:
    if basename and has_local_hook_implementation(content, basename):
        return False
    return any(marker in content for marker in WRAPPER_MARKERS)


def _resolve_ts_path(base_dir: Path, rel_import: str) -> Path | None:
    raw = (base_dir / rel_import).resolve()
    candidates = [raw, raw.with_suffix(".ts"), raw.with_suffix(".tsx")]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def is_thin_wrapper(file_path: Path, content: str, *, depth: int = 0) -> bool:
    if is_thin_wrapper_content(content, basename=file_path.name):
        return True
    if depth >= 4:
        return False

    lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("//")
    ]
    if not lines:
        return False

    compact = re.sub(r"\s+", " ", content)
    reexport_targets = re.findall(
        r"export(?:\s+type\s+\{[^}]+\}|\s+\{[^}]+\}|\s+\*\s+as\s+\w+|\s+\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        compact,
    )
    has_local_impl = bool(re.search(r"\b(function|class)\s+\w+", content))
    if reexport_targets and not has_local_impl:
        return all(
            is_thin_wrapper(
                target,
                target.read_text(encoding="utf-8", errors="ignore"),
                depth=depth + 1,
            )
            for rel in reexport_targets
            if (target := _resolve_ts_path(file_path.parent, rel)) is not None
        )

    export_lines = [line for line in lines if line.startswith("export ") and " from " in line]
    if len(export_lines) != len(lines):
        return False

    for line in export_lines:
        match = re.search(r"from\s+['\"]([^'\"]+)['\"]", line)
        if not match:
            return False
        target = _resolve_ts_path(file_path.parent, match.group(1))
        if target is None:
            return False
        target_content = target.read_text(encoding="utf-8", errors="ignore")
        if not is_thin_wrapper(target, target_content, depth=depth + 1):
            return False

    return True


def scan_duplicate_components(plugin_dir: Path, *, strict: bool) -> list[Finding]:
    plugin_name = plugin_dir.name
    findings: list[Finding] = []
    src = plugin_dir / "src"
    if not src.is_dir():
        return findings

    for file_path in src.rglob("*"):
        if file_path.name not in DUPLICATE_COMPONENT_BASENAMES:
            continue
        if file_path.suffix not in {".tsx", ".ts"}:
            continue

        rel = file_path.relative_to(plugin_dir).as_posix()
        allow_key = (plugin_name, file_path.name)
        if allow_key in LOCAL_IMPLEMENTATION_ALLOWLIST:
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if is_thin_wrapper(file_path, content):
            continue

        level = "error" if (strict or file_path.name == "HelpTooltip.tsx") else "warning"
        findings.append(
            Finding(
                level=level,
                plugin=plugin_name,
                message=(
                    f"{rel}: implementação local de {file_path.name} "
                    f"(esperado wrapper @delpi/plugin-ui ou allowlist documentada)"
                ),
            )
        )
    return findings


def scan_local_pagination_utils(plugin_dir: Path) -> list[Finding]:
    plugin_name = plugin_dir.name
    findings: list[Finding] = []
    for rel in ("src/utils/paginationPages.ts", "src/utils/paginationPages.tsx"):
        file_path = plugin_dir / rel
        if not file_path.is_file():
            continue
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if is_thin_wrapper(file_path, content):
            continue
        findings.append(
            Finding(
                level="error",
                plugin=plugin_name,
                message=f"{rel}: utilitário duplicado — usar @delpi/plugin-ui",
            )
        )
    return findings


def plugin_uses_plugin_ui(plugin_dir: Path) -> bool:
    haystack_parts: list[str] = []
    for name in (*VITE_CONFIG_NAMES, *ENTRY_FILES):
        file_path = plugin_dir / name
        if file_path.is_file():
            haystack_parts.append(file_path.read_text(encoding="utf-8", errors="ignore"))

    src = plugin_dir / "src"
    if src.is_dir():
        for file_path in src.rglob("*"):
            if file_path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            if "@delpi/plugin-ui" in text or "plugin-ui/src/styles.css" in text:
                haystack_parts.append(text)

    return any("@delpi/plugin-ui" in chunk for chunk in haystack_parts)


# Chamada real na config. Comentário ou identificador solto não integra o remote.
_FEDERATION_REMOTE_CALL = re.compile(r"remotes\s*:\s*pluginUiRemote\s*\(")
_PREPARE_REMOTE_CALL = re.compile(r"\bpreparePluginUiRemote\s*\(")
_PLUGIN_UI_STYLE_IMPORT = re.compile(
    r"""import\s*(?:\(\s*)?['"](?:@delpi/plugin-ui/styles|[^'"]*plugin-ui/src/styles\.css)['"]"""
)


def _strip_code_comments(source: str) -> str:
    """Remove comentários JS/TS preservando strings e quebras de linha."""
    out: list[str] = []
    i = 0
    n = len(source)
    while i < n:
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            if end < 0:
                out.append("\n" * source[i:].count("\n"))
                break
            chunk = source[i : end + 2]
            out.append("\n" * chunk.count("\n"))
            i = end + 2
            continue
        if source.startswith("//", i):
            end = source.find("\n", i)
            if end < 0:
                break
            out.append("\n")
            i = end + 1
            continue
        if source[i] in {"'", '"', "`"}:
            quote = source[i]
            out.append(quote)
            i += 1
            while i < n:
                if source[i] == "\\":
                    out.append(source[i : i + 2])
                    i += 2
                    continue
                out.append(source[i])
                if source[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        out.append(source[i])
        i += 1
    return "".join(out)


def _vite_config_text(plugin_dir: Path) -> str:
    for name in VITE_CONFIG_NAMES:
        file_path = plugin_dir / name
        if file_path.is_file():
            return file_path.read_text(encoding="utf-8", errors="ignore")
    return ""


def _has_vite_config(plugin_dir: Path) -> bool:
    return any((plugin_dir / name).is_file() for name in VITE_CONFIG_NAMES)


def _entry_text(plugin_dir: Path) -> str:
    chunks: list[str] = []
    for name in ENTRY_FILES:
        file_path = plugin_dir / name
        if file_path.is_file():
            chunks.append(file_path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def _package_role(plugin_dir: Path) -> str:
    """`mfe` declara Vite/bootstrap/Dockerfile. Biblioteca do manifesto ou peer sem app não declara remote."""
    libraries = {entry["directory"] for entry in load_manifest().get("libraries", [])}
    if plugin_dir.name in libraries:
        return "library"
    if _has_vite_config(plugin_dir):
        return "mfe"
    if (plugin_dir / "src" / "bootstrap.tsx").is_file() or (plugin_dir / "Dockerfile").is_file():
        return "mfe"
    return "library"


def _federation_remote_configured(vite_text: str) -> bool:
    return _FEDERATION_REMOTE_CALL.search(_strip_code_comments(vite_text)) is not None


def _plugin_ui_styles_configured(entry_text: str) -> bool:
    code = _strip_code_comments(entry_text)
    return (
        _PREPARE_REMOTE_CALL.search(code) is not None
        or _PLUGIN_UI_STYLE_IMPORT.search(code) is not None
    )


def scan_integration(plugin_dir: Path) -> list[Finding]:
    if not plugin_uses_plugin_ui(plugin_dir):
        return []

    # Biblioteca (manifesto ou pacote sem app). O MFE hospedeiro declara o remote.
    if _package_role(plugin_dir) == "library":
        return []

    plugin_name = plugin_dir.name
    findings: list[Finding] = []
    if not _has_vite_config(plugin_dir):
        findings.append(
            Finding(
                level="error",
                plugin=plugin_name,
                message="MFE consome @delpi/plugin-ui mas não declara vite.config.*",
            )
        )
        return findings

    if not _federation_remote_configured(_vite_config_text(plugin_dir)):
        findings.append(
            Finding(
                level="error",
                plugin=plugin_name,
                message=(
                    "consome @delpi/plugin-ui mas o vite.config.* não chama "
                    "remotes: pluginUiRemote()"
                ),
            )
        )

    if not _plugin_ui_styles_configured(_entry_text(plugin_dir)):
        findings.append(
            Finding(
                level="error",
                plugin=plugin_name,
                message=(
                    "consome @delpi/plugin-ui mas o entry não chama preparePluginUiRemote() "
                    "nem importa @delpi/plugin-ui/styles"
                ),
            )
        )

    return findings


def audit(*, strict: bool) -> list[Finding]:
    manifest = load_manifest()
    findings: list[Finding] = []

    for plugin_dir in plugin_candidates(manifest):
        findings.extend(scan_duplicate_components(plugin_dir, strict=strict))
        findings.extend(scan_local_pagination_utils(plugin_dir))
        findings.extend(scan_integration(plugin_dir))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Modo CI (exit 1 se houver erros bloqueantes).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Trata toda duplicata catalogada como erro (não só HelpTooltip).",
    )
    args = parser.parse_args()

    findings = audit(strict=args.strict)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]

    if findings:
        print("[auditoria plugin-ui] achados:")
        for finding in findings:
            prefix = "ERRO" if finding.level == "error" else "AVISO"
            print(f"  [{prefix}] {finding.plugin}: {finding.message}")
    else:
        print("[OK] Nenhuma duplicata bloqueante de @delpi/plugin-ui.")

    if warnings and not errors:
        print(f"[OK] {len(warnings)} aviso(s) de migração pendente (não bloqueiam CI).")

    if args.check and errors:
        print(
            "\nDoc: plugins/plugin-ui/docs/migration-catalog.md · "
            "Gate Docker: scripts/ci/check_plugin_docker_shared_libraries.py",
            file=sys.stderr,
        )
        return 1

    if args.strict and (errors or warnings):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
