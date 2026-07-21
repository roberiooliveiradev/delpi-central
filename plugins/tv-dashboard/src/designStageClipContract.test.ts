import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

function ruleBody(css: string, selector: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`(^|[\\s}])${escaped}\\s*\\{([\\s\\S]*?)\\}`, "m"));
  return match?.[2] ?? "";
}

/**
 * Contrato de clip editor ≠ TV:
 * - Editor (palco): overflow visible — pasteboard; itens podem ficar sobre a moldura.
 * - TV/prévia: overflow hidden — retângulo de design clipado (o que vai ao ar).
 *
 * Anti-padrão: forçar overflow:hidden no `.td-composer__canvas` «para WYSIWYG»
 * (corta logo/IDD/handles no canto do palco).
 */
describe("design stage clip contract (editor pasteboard ≠ TV clip)", () => {
  it("canvas do editor NÃO clipa; comunicado/TV clipam", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const editorCss = readFileSync(join(here, "index.css"), "utf8");
    const presentationCss = readFileSync(
      join(here, "../../tv-dashboard-presentation/src/native-screens.css"),
      "utf8",
    );
    const comunicadoCss = readFileSync(
      join(here, "../../plugin-ui/src/styles/comunicado-stage.css"),
      "utf8",
    );

    const canvasBody = ruleBody(editorCss, ".dashboard-tv-dashboard .td-composer__canvas");
    expect(canvasBody).toMatch(/^\s*overflow:\s*visible\s*;/m);
    expect(canvasBody).not.toMatch(/^\s*overflow:\s*hidden\s*;/m);

    const comunicadoBody = ruleBody(comunicadoCss, ".delpi-ui-comunicado");
    expect(comunicadoBody).toMatch(/^\s*overflow:\s*hidden\s*;/m);

    const stageBody = ruleBody(presentationCss, ".tdp-design-viewport__stage");
    expect(stageBody).toMatch(/^\s*overflow:\s*hidden\s*;/m);
  });
});
