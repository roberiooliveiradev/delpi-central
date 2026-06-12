from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal

from tm_app.application.services.json_backup_service import JsonBackupService
from tm_app.core.serialize import json_safe

ExportMode = Literal["replace", "merge"]


def load_payload(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Arquivo não encontrado: {path}")
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit("JSON raiz deve ser um objeto.")
    return data


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(json_safe(payload), ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def print_preview(result: dict[str, Any]) -> None:
    if not result.get("valid"):
        print("Pacote inválido:", file=sys.stderr)
        for err in result.get("errors") or []:
            print(f"  - {err}", file=sys.stderr)
        raise SystemExit(1)

    mode = result.get("mode")
    print(f"Modo: {mode}")
    print(f"Contagens atuais: {result.get('current_counts')}")
    print(f"Contagens no JSON: {result.get('import_counts')}")
    print("Entidades:")
    for key, stats in (result.get("entities") or {}).items():
        print(
            f"  {key}: total={stats.get('total')} "
            f"insert={stats.get('insert')} update={stats.get('update')} skip={stats.get('skip')}"
        )


def cmd_export(args: argparse.Namespace) -> None:
    service = JsonBackupService()
    bundle = service.export_bundle()
    out = Path(args.output)
    write_payload(out, bundle)
    counts = bundle.get("counts") or {}
    print(f"Exportado: {out.resolve()}")
    print(f"schema_version={bundle.get('schema_version')} exported_at={bundle.get('exported_at')}")
    for key, total in sorted(counts.items()):
        print(f"  {key}: {total}")


def cmd_preview(args: argparse.Namespace) -> None:
    payload = load_payload(Path(args.input))
    result = JsonBackupService().preview(payload, args.mode, args.format)
    print_preview(result)


def cmd_apply(args: argparse.Namespace) -> None:
    payload = load_payload(Path(args.input))
    service = JsonBackupService()
    preview = service.preview(payload, args.mode, args.format)
    print_preview(preview)

    if args.mode == "replace" and not args.yes:
        print(
            "\nModo replace apaga todo o cadastro antes de importar. "
            "Use --yes para confirmar.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    result = service.apply(payload, args.mode, args.format)
    recalc = result.get("recalc") or {}
    print("\nImportação concluída.")
    print(f"Recálculo dashboard: {recalc.get('status', recalc)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export/import cadastro Transformômetro (JSON backup schema 1.1)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    export_p = sub.add_parser("export", help="Exporta cadastro do Postgres para JSON.")
    export_p.add_argument(
        "-o",
        "--output",
        required=True,
        help="Caminho do arquivo JSON de saída.",
    )
    export_p.set_defaults(func=cmd_export)

    preview_p = sub.add_parser("preview", help="Valida JSON e mostra diff de importação.")
    preview_p.add_argument("-i", "--input", required=True, help="Arquivo JSON exportado.")
    preview_p.add_argument(
        "--mode",
        choices=("replace", "merge"),
        default="replace",
        help="replace=substituir tudo; merge=upsert por PK (default: replace).",
    )
    preview_p.add_argument(
        "--format",
        choices=("auto", "modern", "legacy"),
        default="auto",
        dest="format",
        help="auto=detectar; legacy=JSON 1.1; modern=Playbook 18 (default: auto).",
    )
    preview_p.set_defaults(func=cmd_preview)

    apply_p = sub.add_parser("apply", help="Importa JSON no Postgres e recalcula dashboard.")
    apply_p.add_argument("-i", "--input", required=True, help="Arquivo JSON exportado.")
    apply_p.add_argument(
        "--mode",
        choices=("replace", "merge"),
        default="replace",
        help="replace=substituir tudo; merge=upsert por PK (default: replace).",
    )
    apply_p.add_argument(
        "--format",
        choices=("auto", "modern", "legacy"),
        default="auto",
        dest="format",
        help="auto=detectar; legacy=JSON 1.1; modern=Playbook 18 (default: auto).",
    )
    apply_p.add_argument(
        "--yes",
        action="store_true",
        help="Obrigatório em mode=replace (confirma truncate do cadastro).",
    )
    apply_p.set_defaults(func=cmd_apply)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
