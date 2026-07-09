#!/usr/bin/env python3
"""Garante que plugins com dependência de biblioteca compartilhada a declarem no Dockerfile.

Uso:
  python3 scripts/ci/check_plugin_docker_shared_libraries.py
  python3 scripts/ci/check_plugin_docker_shared_libraries.py --check

Exit 0 = OK; exit 1 = consumidor sem COPY ou contexto Compose incorreto.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS_DIR = ROOT / "plugins"
MANIFEST_PATH = PLUGINS_DIR / "shared-libraries.manifest.json"
COMPOSE_FILES = [
    ROOT / "infra" / "docker-compose.yml",
    ROOT / "infra" / "docker-compose.dev.yml",
]

SCAN_GLOBS = (
    "vite.config.ts",
    "vite.config.js",
    "vite.config.mts",
    "src/main.tsx",
    "src/bootstrap.tsx",
)


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def library_directories(manifest: dict) -> set[str]:
    return {entry["directory"] for entry in manifest["libraries"]}


def plugin_candidates(manifest: dict) -> list[Path]:
    lib_dirs = library_directories(manifest)
    plugins: list[Path] = []
    for path in sorted(PLUGINS_DIR.iterdir()):
        if not path.is_dir() or path.name in lib_dirs:
            continue
        if (path / "package.json").exists():
            plugins.append(path)
    return plugins


def collect_plugin_sources(plugin_dir: Path) -> str:
    chunks: list[str] = []
    for name in SCAN_GLOBS:
        file_path = plugin_dir / name
        if file_path.is_file():
            chunks.append(file_path.read_text(encoding="utf-8", errors="ignore"))
    src = plugin_dir / "src"
    if src.is_dir():
        for file_path in src.rglob("*"):
            if file_path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            if any(
                token in text
                for token in ("@delpi/", "plugin-ui/", "tv-dashboard-presentation")
            ):
                chunks.append(text)
    return "\n".join(chunks)


def detect_shared_dependencies(plugin_dir: Path, manifest: dict) -> set[str]:
    haystack = collect_plugin_sources(plugin_dir)
    deps: set[str] = set()
    for entry in manifest["libraries"]:
        if any(marker in haystack for marker in entry["markers"]):
            deps.add(entry["directory"])
    return deps


def dockerfile_copies_directory(dockerfile: Path, directory: str) -> bool:
    content = dockerfile.read_text(encoding="utf-8", errors="ignore")
    patterns = (
        rf"COPY\s+{re.escape(directory)}\s",
        rf"COPY\s+{re.escape(directory)}/",
    )
    return any(re.search(pattern, content, flags=re.MULTILINE) for pattern in patterns)


def dockerfile_uses_shared_builder(dockerfile: Path, manifest: dict) -> bool:
    content = dockerfile.read_text(encoding="utf-8", errors="ignore")
    image = str(manifest.get("sharedBuilderImage") or "delpi-plugins-shared-builder:local")
    markers = (
        "SHARED_LIBS_BUILDER",
        image,
        "Dockerfile.shared-libs-builder",
    )
    return any(marker in content for marker in markers)


def library_entries_by_directory(manifest: dict) -> dict[str, dict]:
    return {entry["directory"]: entry for entry in manifest["libraries"]}


def vite_declares_federation_remote(plugin_dir: Path, library_entry: dict) -> bool:
    markers = list(library_entry.get("remoteMarkers") or [])
    remote_entry = library_entry.get("remoteEntry")
    if remote_entry:
        markers.append(remote_entry)
    if not markers:
        return False

    for name in ("vite.config.ts", "vite.config.js", "vite.config.mts"):
        file_path = plugin_dir / name
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if any(marker in text for marker in markers if marker):
            return True
    return False


def federation_remote_satisfied(
    plugin_dir: Path,
    directory: str,
    manifest: dict,
) -> bool:
    library_entry = library_entries_by_directory(manifest).get(directory)
    if not library_entry:
        return False
    if library_entry.get("consumptionMode") != "federation-remote":
        return False
    return vite_declares_federation_remote(plugin_dir, library_entry)


def compose_build_context(plugin_name: str) -> str | None:
    dockerfile_needle = f"{plugin_name}/Dockerfile"
    for compose_path in COMPOSE_FILES:
        if not compose_path.is_file():
            continue
        text = compose_path.read_text(encoding="utf-8", errors="ignore")
        blocks = re.split(r"\n\s{2}\w", text)
        for block in blocks:
            if dockerfile_needle not in block:
                continue
            match = re.search(r"context:\s*(\S+)", block)
            if match:
                return match.group(1).rstrip("/")
    return None


def validate(manifest: dict) -> list[str]:
    errors: list[str] = []
    required_context = manifest.get("requiredBuildContext", "../plugins").rstrip("/")

    for plugin_dir in plugin_candidates(manifest):
        plugin_name = plugin_dir.name
        dockerfile = plugin_dir / "Dockerfile"
        if not dockerfile.is_file():
            continue

        deps = detect_shared_dependencies(plugin_dir, manifest)
        if not deps:
            continue

        if dockerfile_uses_shared_builder(dockerfile, manifest):
            compose_context = compose_build_context(plugin_name)
            if compose_context is not None:
                normalized = compose_context.rstrip("/")
                if not normalized.endswith("/plugins"):
                    errors.append(
                        f"{plugin_name}: docker-compose context={compose_context!r} — "
                        f"consumidor de biblioteca compartilhada exige context {required_context!r}."
                    )
            continue

        lib_by_dir = library_entries_by_directory(manifest)
        uses_builder = dockerfile_uses_shared_builder(dockerfile, manifest)
        missing: list[str] = []
        for directory in sorted(deps):
            entry = lib_by_dir.get(directory, {})
            if uses_builder or dockerfile_copies_directory(dockerfile, directory):
                continue
            if (
                entry.get("consumptionMode") == "federation-remote"
                and vite_declares_federation_remote(plugin_dir, entry)
            ):
                continue
            if entry.get("consumptionMode") == "federation-remote":
                missing.append(
                    f"{directory} (COPY, shared builder ou pluginUiRemote() em vite.config)"
                )
            else:
                missing.append(directory)

        if missing:
            errors.append(
                f"{plugin_name}/Dockerfile: biblioteca(s) compartilhada(s) não satisfeita(s): "
                f"{', '.join(missing)}. "
                f"Bundled: COPY ou shared builder. Remote: remotes em vite.config.ts."
            )

        compose_context = compose_build_context(plugin_name)
        if compose_context is not None:
            normalized = compose_context.rstrip("/")
            if not normalized.endswith("/plugins"):
                errors.append(
                    f"{plugin_name}: docker-compose context={compose_context!r} — "
                    f"consumidor de biblioteca compartilhada exige context {required_context!r}."
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Alias explícito para CI (mesmo comportamento padrão).",
    )
    _args = parser.parse_args()

    if not MANIFEST_PATH.is_file():
        print(f"[ERRO] Manifesto ausente: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = load_manifest()
    errors = validate(manifest)
    if errors:
        print("[ERRO] Verificação de bibliotecas compartilhadas no Docker falhou:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print(
            "\nDoc: plugins/docker/README.md · Manifesto: plugins/shared-libraries.manifest.json",
            file=sys.stderr,
        )
        return 1

    print("[OK] Plugins consumidores de bibliotecas compartilhadas têm Dockerfile/Compose alinhados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
