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
 * Contrato de paridade editor ↔ TV:
 * - Editor (`.td-composer__canvas`): overflow visible — pasteboard.
 * - Comunicado / `__design`: overflow visible na moldura.
 * - Pasteboard na TV: bleed em `DesignViewportStage` (não só CSS overflow).
 *
 * Anti-padrão: overflow:hidden no canvas do editor «para WYSIWYG».
 */
describe("design stage clip contract (editor ↔ TV parity)", () => {
  it("canvas, comunicado e design-viewport__design NÃO clipam a moldura", () => {
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
    const viewportSrc = readFileSync(
      join(here, "../../tv-dashboard-presentation/src/DesignViewportStage.tsx"),
      "utf8",
    );

    const canvasBody = ruleBody(editorCss, ".dashboard-tv-dashboard .td-composer__canvas");
    expect(canvasBody).toMatch(/^\s*overflow:\s*visible\s*;/m);
    expect(canvasBody).not.toMatch(/^\s*overflow:\s*hidden\s*;/m);

    const comunicadoBody = ruleBody(comunicadoCss, ".delpi-ui-comunicado");
    expect(comunicadoBody).toMatch(/^\s*overflow:\s*visible\s*;/m);
    expect(comunicadoBody).not.toMatch(/^\s*overflow:\s*hidden\s*;/m);

    const designBody = ruleBody(presentationCss, ".tdp-design-viewport__design");
    expect(designBody).toMatch(/^\s*overflow:\s*visible\s*;/m);

    expect(viewportSrc).toMatch(/DESIGN_VIEWPORT_BLEED_RATIO/);
    expect(viewportSrc).toMatch(/computeDesignViewportBleedSize/);
    expect(viewportSrc).toMatch(/tdp-design-viewport__design/);

    expect(comunicadoBody).toMatch(/font-size:\s*16px/);
    expect(comunicadoCss).toMatch(/\.tdp-stage--animate-entrances/);
  });
});
