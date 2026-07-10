#!/usr/bin/env node
/**
 * Verifica react/react-dom instalados e declarados = REACT_PINNED_VERSION.
 * Uso: node plugins/vite/verify-react-pinned-version.mjs [portal plugins/dashboard-supplies ...]
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, "../..");
const PIN = fs
  .readFileSync(path.join(__dirname, "reactPinnedVersion.ts"), "utf8")
  .match(/REACT_PINNED_VERSION = "([^"]+)"/)?.[1];

const dirs =
  process.argv.length > 2
    ? process.argv.slice(2).map((d) => path.resolve(REPO, d))
    : [
        path.join(REPO, "portal"),
        path.join(REPO, "plugins/plugin-ui"),
        path.join(REPO, "plugins/dashboard-supplies"),
        path.join(REPO, "plugins/controle-retrabalhos"),
      ];

let failed = false;

for (const dir of dirs) {
  const pkg = path.join(dir, "package.json");
  if (!fs.existsSync(pkg)) {
    console.error("skip (sem package.json):", dir);
    continue;
  }
  const declared = JSON.parse(fs.readFileSync(pkg, "utf8"));
  for (const key of ["react", "react-dom"]) {
    const v = declared.dependencies?.[key] ?? declared.devDependencies?.[key];
    if (v && v !== PIN) {
      console.error(`FAIL declare ${path.relative(REPO, dir)} ${key}=${v}`);
      failed = true;
    }
  }
  for (const key of ["react", "react-dom"]) {
    const mod = path.join(dir, "node_modules", key, "package.json");
    if (!fs.existsSync(mod)) {
      console.warn(`WARN sem node_modules/${key}:`, path.relative(REPO, dir));
      continue;
    }
    const installed = JSON.parse(fs.readFileSync(mod, "utf8")).version;
    if (installed !== PIN) {
      console.error(`FAIL installed ${path.relative(REPO, dir)} ${key}=${installed}`);
      failed = true;
    }
  }
}

const sync = spawnSync("node", [path.join(__dirname, "sync-react-pinned-version.mjs"), "--check"], {
  stdio: "inherit",
});
if (sync.status !== 0) failed = true;

if (failed) process.exit(1);
console.log(`OK: React ${PIN} alinhado`);
