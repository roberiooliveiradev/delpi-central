/**
 * Contrato CSS da row de medida da TopBar: largura intrínseca (max-content),
 * sem min-width:100% — necessário para histerese de reexpansão do overflow.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const cssPath = join(__dirname, "../../styles/top-bar.css");

function measureRowRule(css) {
  const start = css.indexOf(".delpi-ui-topbar__row--measure {");
  assert.ok(start >= 0, "regra .delpi-ui-topbar__row--measure não encontrada");
  const end = css.indexOf("}", start);
  return css.slice(start, end + 1);
}

describe("topBarMeasureRow (structural)", () => {
  const css = readFileSync(cssPath, "utf8");
  const rule = measureRowRule(css);

  it("usa width: max-content para medir conteúdo real", () => {
    assert.match(rule, /width:\s*max-content/);
  });

  it("não força min-width: 100% (quebra reexpansão com histerese)", () => {
    assert.doesNotMatch(rule, /min-width:\s*100%/);
  });

  it("define min-width: 0 para não herdar stretch do flex host", () => {
    assert.match(rule, /min-width:\s*0/);
  });
});
