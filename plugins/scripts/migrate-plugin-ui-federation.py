#!/usr/bin/env python3
"""Migração mecânica de um MFE para consumir @delpi/plugin-ui via Module Federation.

Uso:
  python3 plugins/scripts/migrate-plugin-ui-federation.py transformometro maintenance
  python3 plugins/scripts/migrate-plugin-ui-federation.py --all-remaining

Doc: plugins/plugin-ui/docs/module-federation.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ROOT / "plugins"

DOCKERFILE_TEMPLATE = """\
# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app
{extra_copy}
COPY {name}/package*.json ./{name}/
RUN --mount=type=cache,target=/root/.npm \\
    cd {name} && npm install

COPY {name} ./{name}
COPY vite ./vite

WORKDIR /app/{name}
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/{name}/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""

VITE_TEMPLATE = """\
{header}import {{ defineConfig }} from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
{path_import}
import {{
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  reactResolveAliases,{vitest_import}
}} from "../vite/federation.shared";

export default defineConfig({{
  plugins: [
    federation({{
      name: "{name}",
      filename: "remoteEntry.js",
      remotes: pluginUiRemote(),
      exposes: {{
        "./App": "./src/bootstrap.tsx",
      }},
      shared: [...FEDERATION_SHARED_REACT],
    }}),
    react(),
  ],
  resolve: {{
    alias: {{
{extra_aliases}      ...reactResolveAliases(__dirname),
    }},
    dedupe: ["react", "react-dom"],
  }},
  base: "{base}",
  build: {{
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  }},{test_block}
}});
"""

VITE_TEST_BLOCK = """
  test: {
    environment: "node",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    alias: pluginUiTestAliases(__dirname),
  },
"""

TSCONFIG_PATHS = """\
    "paths": {
      "@delpi/plugin-ui": ["../plugin-ui/src/index.ts"],
      "@delpi/plugin-ui/index": ["../plugin-ui/src/index.ts"],
      "@delpi/plugin-ui/styles": ["../plugin-ui/src/styles.css"]
    }"""

# Plugins com alias extra além de plugin-ui (bundled).
EXTRA_VITE_ALIASES: dict[str, str] = {
    "tv-dashboard": """      "@delpi/tv-dashboard-presentation": path.resolve(
        __dirname,
        "../tv-dashboard-presentation/src/index.ts",
      ),
""",
}

EXTRA_DOCKER_COPY: dict[str, str] = {
    "tv-dashboard": """\
COPY tv-dashboard-presentation/package*.json ./tv-dashboard-presentation/
RUN --mount=type=cache,target=/root/.npm \\
    cd tv-dashboard-presentation && npm install

COPY tv-dashboard-presentation ./tv-dashboard-presentation

""",
}

LOT_2B = [
    "transformometro",
    "quality-action-plans",
    "cadastro-kaizen",
    "maintenance",
    "eficiencia-fabril",
    "minha-delpi-chat",
    "auditoria-5s",
    "inspecoes-entrada",
    "pedidos-venda-abertos",
    "propostas-comerciais",
    "financeiro-centro-custo",
    "strategic-indicators",
    "customer-experience",
    "cultura-delpi",
    "central-agendamento",
    "quality-labels",
    "tv-dashboard",
]

ALREADY_MIGRATED = {
    "controle-retrabalhos",
    "dashboard-production",
    "dashboard-commercial",
    "dashboard-engineering",
    "dashboard-financial",
    "dashboard-hr",
    "dashboard-lmps",
    "dashboard-quality",
    "dashboard-supplies",
    "plugin-ui",
}


def migrate_plugin(name: str) -> None:
    plugin_dir = PLUGINS / name
    if not (plugin_dir / "package.json").is_file():
        raise SystemExit(f"Plugin não encontrado: {name}")

    vite_path = plugin_dir / "vite.config.ts"
    original_vite = vite_path.read_text(encoding="utf-8") if vite_path.is_file() else ""
    had_vitest = "vitest/config" in original_vite

    extra_aliases = EXTRA_VITE_ALIASES.get(name, "")
    path_import = "import path from \"node:path\";\n" if extra_aliases else ""
    if had_vitest:
        header = '/// <reference types="vitest/config" />\n'
        test_block = VITE_TEST_BLOCK
        vitest_import = "\n  pluginUiTestAliases,"
    else:
        header = ""
        test_block = ""
        vitest_import = ""

    base_match = re.search(r'base:\s*"([^"]+)"', original_vite)
    base = base_match.group(1) if base_match else f"/apps/{name}/"

    vite_path.write_text(
        VITE_TEMPLATE.format(
            header=header,
            path_import=path_import,
            name=name,
            base=base,
            extra_aliases=extra_aliases,
            test_block=test_block,
            vitest_import=vitest_import,
        ),
        encoding="utf-8",
    )

    extra_copy = EXTRA_DOCKER_COPY.get(name, "")
    (plugin_dir / "Dockerfile").write_text(
        DOCKERFILE_TEMPLATE.format(name=name, extra_copy=extra_copy),
        encoding="utf-8",
    )

    _migrate_styles_entry(plugin_dir / "src/bootstrap.tsx")
    _migrate_styles_entry(plugin_dir / "src/main.tsx")

    tsconfig = plugin_dir / "tsconfig.app.json"
    if tsconfig.is_file():
        content = tsconfig.read_text(encoding="utf-8")
        content = re.sub(
            r'"paths":\s*\{[^}]*\}',
            TSCONFIG_PATHS,
            content,
            count=1,
        )
        tsconfig.write_text(content, encoding="utf-8")

    vite_env = plugin_dir / "src/vite-env.d.ts"
    if vite_env.is_file():
        content = vite_env.read_text(encoding="utf-8")
        if "@delpi/plugin-ui/styles" not in content:
            content = content.rstrip() + '\n\ndeclare module "@delpi/plugin-ui/styles";\n'
            vite_env.write_text(content, encoding="utf-8")

    for src_file in (plugin_dir / "src").rglob("*"):
        if src_file.suffix not in {".ts", ".tsx"}:
            continue
        content = src_file.read_text(encoding="utf-8")
        updated = content.replace('from "@delpi/plugin-ui"', 'from "@delpi/plugin-ui/index"')
        updated = updated.replace("from '@delpi/plugin-ui'", "from '@delpi/plugin-ui/index'")
        if updated != content:
            src_file.write_text(updated, encoding="utf-8")

    print(f"[OK] {name}")


def _migrate_styles_entry(path: Path) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"import\s+['\"]\.\./\.\./plugin-ui/src/styles\.css['\"];\n",
        "",
        text,
    )
    if 'await import("@delpi/plugin-ui/styles")' in text:
        path.write_text(text, encoding="utf-8")
        return
    if path.name == "bootstrap.tsx":
        if 'import "./index.css";' in text:
            text = text.replace(
                'import "./index.css";',
                'import "./index.css";\n\nawait import("@delpi/plugin-ui/styles");',
            )
        else:
            lines = text.split("\n", 1)
            text = lines[0] + '\n\nawait import("@delpi/plugin-ui/styles");\n' + (lines[1] if len(lines) > 1 else "")
    path.write_text(text, encoding="utf-8")


def remaining_plugins() -> list[str]:
    pending: list[str] = []
    for path in sorted(PLUGINS.iterdir()):
        if not path.is_dir() or path.name in ALREADY_MIGRATED:
            continue
        vite = path / "vite.config.ts"
        if not vite.is_file():
            continue
        text = vite.read_text(encoding="utf-8")
        if 'pluginUiRemote()' in text:
            continue
        if '"@delpi/plugin-ui": path.resolve' in text or "'@delpi/plugin-ui': path.resolve" in text:
            pending.append(path.name)
    return pending


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1

    if argv[1] == "--all-remaining":
        names = remaining_plugins()
        if not names:
            print("Nenhum plugin pendente.")
            return 0
        print(f"Migrando {len(names)} plugin(s): {', '.join(names)}")
    elif argv[1] == "--lot-2b":
        names = LOT_2B
    else:
        names = argv[1:]

    for name in names:
        migrate_plugin(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
