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
 * Contrato de paridade editor ↔ TV no overflow da moldura de design:
 * - Editor (`.td-composer__canvas`): overflow visible — pasteboard.
 * - TV/prévia (`.delpi-ui-comunicado`, `.tdp-design-viewport__stage`): overflow
 *   visible — mesmos itens fora da moldura aparecem no letterbox.
 * - Clip físico: só `.tdp-stage` / container externo do DesignViewportStage.
 *
 * Anti-padrão: overflow:hidden no canvas do editor «para WYSIWYG», ou clip na
 * moldura de design na TV (quebra igualdade edição ↔ apresentação).
 */
describe("design stage clip contract (editor ↔ TV parity)", () => {
  it("canvas, comunicado e design-viewport stage NÃO clipam a moldura", () => {
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
    expect(comunicadoBody).toMatch(/^\s*overflow:\s*visible\s*;/m);
    expect(comunicadoBody).not.toMatch(/^\s*overflow:\s*hidden\s*;/m);

    const stageBody = ruleBody(presentationCss, ".tdp-design-viewport__stage");
    expect(stageBody).toMatch(/^\s*overflow:\s*visible\s*;/m);
    expect(stageBody).not.toMatch(/^\s*overflow:\s*hidden\s*;/m);
  });
});
