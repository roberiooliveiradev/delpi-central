#!/usr/bin/env node
/**
 * Gate: HelpTooltip no Portal Comercial sempre com wrap (help no label/controle, sem ? solto).
 */
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(here, "..");

function listTsxFiles(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const st = statSync(path);
    if (st.isDirectory()) {
      if (name === "node_modules" || name === "dist") continue;
      listTsxFiles(path, out);
    } else if (name.endsWith(".tsx")) {
      out.push(path);
    }
  }
  return out;
}

/** Extrai blocos `<HelpTooltip …>` (self-closing ou com filhos até `</HelpTooltip>`). */
function findHelpTooltipBlocks(source) {
  const blocks = [];
  const re = /<HelpTooltip\b/g;
  let match;
  while ((match = re.exec(source)) !== null) {
    const start = match.index;
    const fromOpen = source.slice(start);
    const selfClose = fromOpen.match(/^<HelpTooltip\b[^>]*\/>/);
    if (selfClose) {
      blocks.push({ text: selfClose[0], index: start });
      continue;
    }
    const endTag = fromOpen.indexOf("</HelpTooltip>");
    assert.ok(endTag > 0, `HelpTooltip sem fechamento em offset ${start}`);
    blocks.push({ text: fromOpen.slice(0, endTag), index: start });
  }
  return blocks;
}

describe("commercial HelpTooltip — wrap obrigatório", () => {
  it("todo HelpTooltip em src/**/*.tsx usa wrap (sem gatilho ? solto)", () => {
    const files = listTsxFiles(srcRoot);
    const violations = [];
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      for (const block of findHelpTooltipBlocks(source)) {
        if (!/\bwrap\b/.test(block.text)) {
          const line = source.slice(0, block.index).split("\n").length;
          violations.push(`${relative(srcRoot, file)}:${line}`);
        }
      }
    }
    assert.deepEqual(
      violations,
      [],
      `HelpTooltip sem wrap (use SectionHintLabel / TitleWithHelp / wrap):\n${violations.join("\n")}`,
    );
  });
});
