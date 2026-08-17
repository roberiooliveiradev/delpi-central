#!/usr/bin/env node
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const srcRoot = join(dirname(fileURLToPath(import.meta.url)), "..");

function filesUnder(directory) {
  const out = [];
  for (const entry of readdirSync(directory)) {
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) out.push(...filesUnder(path));
    else if (/\.(?:tsx?|mjs)$/.test(path)) out.push(path);
  }
  return out;
}

describe("E1.S3 — gate rótulos Filial/código na UI", () => {
  it("não usa label/header Filial nem Filial ${code} em source TSX", () => {
    const forbidden =
      /label=["']Filial["']|header:\s*["']Filial["']|label:\s*["']Filial["']|Filial \$\{|OTD SC|OTD ES|label:\s*["']01["']/;
    for (const file of filesUnder(srcRoot)) {
      if (file.includes(".test.")) continue;
      const source = readFileSync(file, "utf8");
      assert.doesNotMatch(source, forbidden, file);
    }
  });

  it("help de filtros fala em unidade SC/ES", () => {
    const help = readFileSync(join(srcRoot, "content/helpTooltips.ts"), "utf8");
    assert.match(help, /Unidade responsável pelo pedido/);
    assert.match(help, /Santa Catarina e Espírito Santo/);
    assert.doesNotMatch(help, /Filial responsável pelo pedido/);
  });
});
