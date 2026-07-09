#!/usr/bin/env python3
"""Varredura de <select> e <textarea> nativos fora de @delpi/plugin-ui.

Detecta JSX/TSX com controles nativos inline nos plugins MFE. O canônico é
NativeSelectControl / SelectControl / NativeTextAreaControl / Native*Field
(importados de @delpi/plugin-ui ou wrappers finos locais).

Uso:
  python3 scripts/ci/audit_plugin_ui_native_form_controls.py
  python3 scripts/ci/audit_plugin_ui_native_form_controls.py --check
  python3 scripts/ci/audit_plugin_ui_native_form_controls.py --json

Exit 0 = OK; exit 1 = ocorrência fora da allowlist (--check).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS_DIR = ROOT / "plugins"

SCAN_GLOBS = ("**/*.tsx", "**/*.jsx")
NATIVE_SELECT_RE = re.compile(r"<select\b")
NATIVE_TEXTAREA_RE = re.compile(r"<textarea\b")

# Plugins fora do escopo de migração plugin-ui (informativo — não entra na allowlist).
EXCLUDED_PLUGINS = frozenset(
    {
        "plugin-ui",
        "api-delpi-console",
        "public-hub",
        "portal",
    }
)

# Ocorrências conhecidas e aceitas até migração (domínio ou backlog documentado).
# Chave: path relativo a plugins/ (POSIX). Valor: motivo curto.
KNOWN_ALLOWLIST: dict[str, str] = {
    # ——— minha-delpi-chat: UX de conversa / edição inline (fora de FormFieldShell) ———
    "minha-delpi-chat/src/ui/components/composer/ChatInput.tsx": "composer principal — autosize/stream",
    "minha-delpi-chat/src/ui/components/message/ChatMessageEditField.tsx": "edição inline de mensagem",
    "minha-delpi-chat/src/ui/components/canvas/ChatCanvas.tsx": "editor markdown do canvas",
    "minha-delpi-chat/src/ui/components/shared/modal/ChatShortcutPromptDialog.tsx": "prompt rápido modal",
    # ——— minha-delpi-chat: backlog admin/workspace (migrar para chatAdminFormFields) ———
    "minha-delpi-chat/src/ui/components/admin/evaluations/AdminEvaluationsTab.tsx": "backlog: CxNative/chatAdmin",
    "minha-delpi-chat/src/ui/components/admin/guidelines/GuidelineTestPanel.tsx": "backlog: chatAdmin",
    "minha-delpi-chat/src/ui/components/admin/security/AdminSecurityTab.tsx": "backlog: chatAdmin",
    "minha-delpi-chat/src/ui/components/admin/skills/AdminSkillsTab.tsx": "backlog: chatAdmin (2×)",
    "minha-delpi-chat/src/ui/components/workspace/ChatAddContextDialog.tsx": "backlog: workspace forms",
    "minha-delpi-chat/src/ui/components/workspace/ChatProjectSettingsModal.tsx": "backlog: workspace forms",
    "minha-delpi-chat/src/ui/components/workspace/WorkspaceSourceNote.tsx": "backlog: workspace forms",
    "minha-delpi-chat/src/ui/components/workspace/agentBuilder/AgentIcebreakersEditor.tsx": "backlog: ref/onKeyDown",
    "minha-delpi-chat/src/ui/pages/ChatAgentBuilderPage.tsx": "backlog: ref/onKeyDown residual",
    "minha-delpi-chat/src/ui/pages/agent-actions/ActionTestPanel.tsx": "backlog: JSON test panel",
    # ——— demais plugins ———
    "cultura-delpi/src/pages/AdminCulturaPage.tsx": "backlog: sem kit plugin-ui",
    "propostas-comerciais/src/components/ItensTable.tsx": "backlog: célula editável inline",
    "propostas-comerciais/src/components/PropostaComercialPdfExportModal.tsx": "backlog: modal export",
    "tv-dashboard/src/components/ComunicadoEditorTextBlock.tsx": "backlog: bloco rich text deck",
}


@dataclass(frozen=True)
class NativeControlHit:
    plugin: str
    rel_path: str
    line: int
    kind: str  # select | textarea
    allowlisted: bool
    reason: str | None


def iter_source_files(plugin_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(plugin_dir.glob(pattern))
    return sorted({path for path in files if "node_modules" not in path.parts})


def scan_file(plugin: str, path: Path) -> list[NativeControlHit]:
    rel_path = path.relative_to(PLUGINS_DIR).as_posix()
    allow_reason = KNOWN_ALLOWLIST.get(rel_path)
    hits: list[NativeControlHit] = []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return hits

    for index, line in enumerate(lines, start=1):
        kind: str | None = None
        if NATIVE_SELECT_RE.search(line):
            kind = "select"
        elif NATIVE_TEXTAREA_RE.search(line):
            kind = "textarea"
        if kind is None:
            continue

        hits.append(
            NativeControlHit(
                plugin=plugin,
                rel_path=rel_path,
                line=index,
                kind=kind,
                allowlisted=allow_reason is not None,
                reason=allow_reason,
            )
        )

    return hits


def collect_hits() -> list[NativeControlHit]:
    all_hits: list[NativeControlHit] = []
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir():
            continue
        plugin = plugin_dir.name
        if plugin in EXCLUDED_PLUGINS:
            continue
        if not (plugin_dir / "package.json").exists():
            continue
        for source in iter_source_files(plugin_dir):
            all_hits.extend(scan_file(plugin, source))
    return all_hits


def print_report(hits: list[NativeControlHit]) -> None:
    allowlisted = [hit for hit in hits if hit.allowlisted]
    unlisted = [hit for hit in hits if not hit.allowlisted]

    by_plugin: dict[str, list[NativeControlHit]] = {}
    for hit in hits:
        by_plugin.setdefault(hit.plugin, []).append(hit)

    print("Varredura — controles nativos fora de @delpi/plugin-ui")
    print(f"Plugins excluídos: {', '.join(sorted(EXCLUDED_PLUGINS))}")
    print(f"Total: {len(hits)} ({len(allowlisted)} allowlist, {len(unlisted)} novos/bloqueantes)")
    print()

    for plugin in sorted(by_plugin):
        plugin_hits = by_plugin[plugin]
        print(f"## {plugin} ({len(plugin_hits)})")
        for hit in plugin_hits:
            flag = "allowlist" if hit.allowlisted else "NOVO"
            reason = f" — {hit.reason}" if hit.reason else ""
            print(f"  [{flag}] {hit.rel_path}:{hit.line} <{hit.kind}>{reason}")
        print()

    if unlisted:
        print("BLOQUEANTES (fora da allowlist):")
        for hit in unlisted:
            print(f"  {hit.rel_path}:{hit.line} <{hit.kind}>")
    else:
        print("Nenhuma ocorrência nova fora da allowlist.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 se houver ocorrência fora de KNOWN_ALLOWLIST",
    )
    parser.add_argument("--json", action="store_true", help="Saída JSON")
    args = parser.parse_args()

    hits = collect_hits()
    unlisted = [hit for hit in hits if not hit.allowlisted]

    if args.json:
        payload = {
            "excluded_plugins": sorted(EXCLUDED_PLUGINS),
            "allowlist_size": len(KNOWN_ALLOWLIST),
            "total": len(hits),
            "allowlisted": len(hits) - len(unlisted),
            "unlisted": len(unlisted),
            "hits": [asdict(hit) for hit in hits],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_report(hits)

    if args.check and unlisted:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
