#!/usr/bin/env node
/**
 * Alinha react/react-dom em package.json ao REACT_PINNED_VERSION.
 * Uso: node plugins/vite/sync-react-pinned-version.mjs [--check]
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, "../..");
const PIN = fs
  .readFileSync(path.join(__dirname, "reactPinnedVersion.ts"), "utf8")
  .match(/REACT_PINNED_VERSION = "([^"]+)"/)?.[1];

if (!PIN) {
  console.error("Não encontrou REACT_PINNED_VERSION em reactPinnedVersion.ts");
  process.exit(1);
}

const CHECK = process.argv.includes("--check");
const ROOTS = [path.join(REPO, "portal"), path.join(REPO, "plugins")];
const files = [];

for (const root of ROOTS) {
  if (!fs.existsSync(root)) continue;
  if (root.endsWith("portal")) {
    files.push(path.join(root, "package.json"));
    continue;
  }
  for (const name of fs.readdirSync(root)) {
    const pkg = path.join(root, name, "package.json");
    if (fs.existsSync(pkg)) files.push(pkg);
  }
}

let failed = false;

for (const pkgPath of files.sort()) {
  const raw = fs.readFileSync(pkgPath, "utf8");
  const json = JSON.parse(raw);
  let changed = false;

  for (const section of ["dependencies", "devDependencies", "peerDependencies"]) {
    const deps = json[section];
    if (!deps) continue;
    for (const key of ["react", "react-dom"]) {
      if (!(key in deps)) continue;
      if (deps[key] !== PIN) {
        if (CHECK) {
          console.error(`FAIL ${path.relative(REPO, pkgPath)} ${section}.${key}=${deps[key]} (esperado ${PIN})`);
          failed = true;
        } else {
          deps[key] = PIN;
          changed = true;
        }
      }
    }
  }

  if (changed && !CHECK) {
    fs.writeFileSync(pkgPath, JSON.stringify(json, null, 2) + "\n");
    console.log("updated", path.relative(REPO, pkgPath));
  }
}

if (CHECK && !failed) {
  console.log(`OK: react/react-dom = ${PIN} em todos os package.json`);
}

process.exit(failed ? 1 : 0);
