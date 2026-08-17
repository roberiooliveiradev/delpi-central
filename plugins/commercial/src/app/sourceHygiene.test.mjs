import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const appDirectory = dirname(fileURLToPath(import.meta.url));
const sourceRoot = join(appDirectory, "..");
const pluginRoot = join(sourceRoot, "..");

function filesUnder(directory, predicate = () => true) {
  const files = [];
  for (const entry of readdirSync(directory)) {
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) {
      files.push(...filesUnder(path, predicate));
    } else if (predicate(path)) {
      files.push(path);
    }
  }
  return files;
}

describe("higiene estrutural do Commercial", () => {
  it("impede prefixo e root legados em source e estilos", () => {
    const legacyPrefix = String.fromCharCode(112, 118, 97);
    const legacyRoot = ["dashboard", "pedidos", "venda", "abertos"].join("-");
    const forbidden = new RegExp(`${legacyPrefix}|${legacyRoot}`, "i");
    const files = filesUnder(sourceRoot, (path) => /\.(?:ts|tsx|mjs|css)$/.test(path));

    for (const file of files) {
      if (file === fileURLToPath(import.meta.url)) continue;
      assert.doesNotMatch(readFileSync(file, "utf8"), forbidden, file);
    }
  });

  it("impede overrides do kit no CSS do MFE", () => {
    const styles = filesUnder(sourceRoot, (path) => path.endsWith(".css"));
    for (const file of styles) {
      assert.doesNotMatch(readFileSync(file, "utf8"), /\.delpi-ui-[\w-]+/, file);
    }
  });

  it("mantem arquivos e exports mortos removidos", () => {
    const legacyPrefix = String.fromCharCode(112, 118, 97);
    const removedFiles = [
      join(sourceRoot, "components", `${legacyPrefix[0].toUpperCase()}${legacyPrefix.slice(1)}Modal.tsx`),
      join(sourceRoot, "ui", `${legacyPrefix}Kit.tsx`),
      join(sourceRoot, "ui", ["ghost", "Chrome.ts"].join("")),
      join(sourceRoot, "ui", ["state", "Chrome.ts"].join("")),
      join(sourceRoot, "ui", ["table", "Chrome.ts"].join("")),
      join(sourceRoot, "ui", ["commercial", "Kit.tsx"].join("")),
    ];
    for (const file of removedFiles) assert.equal(existsSync(file), false, file);

    const removedSymbols = new RegExp(
      [
        ["Commercial", "Workbench", "Modal"].join(""),
        ["Commercial", "Drawer", "Shell"].join(""),
      ].join("|"),
    );
    for (const file of filesUnder(sourceRoot, (path) => /\.(?:ts|tsx)$/.test(path))) {
      assert.doesNotMatch(readFileSync(file, "utf8"), removedSymbols, file);
    }
  });

  it("mantem helps visiveis sem detalhes de integracao", () => {
    const contentFiles = [
      join(sourceRoot, "content", "helpTooltips.ts"),
      join(sourceRoot, "content", "analyticsContent.ts"),
    ];
    const technicalContent =
      /https?:\/\/|\/(?:apps|api|v\d+)\b|\b(?:GET|POST|PUT|PATCH|DELETE)\b|api-delpi|\bProtheus\b|\b(?:S[A-Z]\d|A[A-Z]{2})\b|\b[A-Z]\d_[A-Z0-9_]+\b|\b[Mm]odal\b/;

    for (const file of contentFiles) {
      assert.doesNotMatch(readFileSync(file, "utf8"), technicalContent, file);
    }
  });
});

