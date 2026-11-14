import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const sources = readdirSync(here)
  .filter((name) => /\.tsx?$/.test(name) && !name.endsWith(".test.ts"))
  .map((name) => ({ name, text: readFileSync(join(here, name), "utf8") }));
const api = readFileSync(join(here, "../../api/satisfactionSurveysApi.ts"), "utf8");
const css = readFileSync(join(here, "../../styles/satisfaction.css"), "utf8");

describe("Pesquisa de Satisfação (A/B) — guardrails estruturais", () => {
  it("MFE só fala com a commercial-api (sem api-delpi)", () => {
    assert.match(api, /commercialApiUrl/);
    assert.doesNotMatch(api, /api-delpi|apiDelpiUrl|API_DELPI/);
    for (const { name, text } of sources) {
      assert.doesNotMatch(text, /api-delpi|apiDelpiUrl|API_DELPI/, name);
    }
  });

  it("não persiste dados da pesquisa no navegador", () => {
    for (const { name, text } of sources) {
      assert.doesNotMatch(text, /localStorage|sessionStorage|document\.cookie/, name);
    }
  });

  it("prévia de e-mail usa somente HTML escapado por buildInviteHtml", () => {
    const preview = sources.find((s) => s.name === "InvitePreview.tsx")?.text ?? "";
    assert.match(preview, /buildInviteHtml/);
    assert.doesNotMatch(preview, /dangerouslySetInnerHTML/);
    for (const { name, text } of sources.filter((s) => s.name.endsWith(".tsx"))) {
      assert.doesNotMatch(text, /dangerouslySetInnerHTML/, name);
    }
  });

  it("CSS é só layout de página: sem seletor do kit", () => {
    assert.doesNotMatch(css, /\.delpi-ui-/);
    assert.doesNotMatch(css, /\.cm-(button|field|dialog|badge|card)\b/);
  });

  it("não implementa resultados/UI-01/05/06/07 nesta fatia", () => {
    for (const { name, text } of sources) {
      assert.doesNotMatch(text, /Ver resultados|response_rate|taxa de resposta/i, name);
    }
  });
});
