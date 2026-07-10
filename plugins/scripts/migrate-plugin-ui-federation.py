#!/usr/bin/env python3
"""Migração mecânica de um MFE para consumir @delpi/plugin-ui via Module Federation.

Uso:
  python3 plugins/scripts/migrate-plugin-ui-federation.py dashboard-production
  python3 plugins/scripts/migrate-plugin-ui-federation.py dashboard-production dashboard-hr

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
import {{ defineConfig }} from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

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
      ...reactResolveAliases(__dirname),
    }},
    dedupe: ["react", "react-dom"],
  }},
  base: "/apps/{name}/",
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


def migrate_plugin(name: str) -> None:
    plugin_dir = PLUGINS / name
    if not (plugin_dir / "package.json").is_file():
        raise SystemExit(f"Plugin não encontrado: {name}")

    vite_path = plugin_dir / "vite.config.ts"
    had_vitest = vite_path.is_file() and "vitest/config" in vite_path.read_text(encoding="utf-8")

    if had_vitest:
        vite_header = '/// <reference types="vitest/config" />\n'
        test_block = VITE_TEST_BLOCK
        vitest_import = "\n  pluginUiTestAliases,"
    else:
        vite_header = ""
        test_block = ""
        vitest_import = ""

    vite_path.write_text(
        vite_header + VITE_TEMPLATE.format(name=name, test_block=test_block, vitest_import=vitest_import),
        encoding="utf-8",
    )

    (plugin_dir / "Dockerfile").write_text(DOCKERFILE_TEMPLATE.format(name=name), encoding="utf-8")

    bootstrap = plugin_dir / "src/bootstrap.tsx"
    if bootstrap.is_file():
        text = bootstrap.read_text(encoding="utf-8")
        text = re.sub(
            r'import\s+"\.\./\.\./plugin-ui/src/styles\.css";\n',
            "",
            text,
        )
        if 'await import("@delpi/plugin-ui/styles")' not in text:
            text = text.replace(
                'import "./index.css";',
                'import "./index.css";\n\nawait import("@delpi/plugin-ui/styles");',
            )
        bootstrap.write_text(text, encoding="utf-8")

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
        if updated != content:
            src_file.write_text(updated, encoding="utf-8")

    print(f"[OK] {name}")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1
    for name in argv[1:]:
        migrate_plugin(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
