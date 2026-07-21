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
 * Contrato WYSIWYG: o retângulo de design do editor e da TV/prévia usam o mesmo clip.
 * Sem isso, sombra/conteúdo na borda parece ok no palco e cortado na apresentação
 * (mesma frame % — percepção de «posição errada»).
 */
describe("design stage clip contract (editor ≡ TV)", () => {
  it("canvas do editor e comunicado/TV clipam overflow", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const editorCss = readFileSync(join(here, "index.css"), "utf8");
    const presentationCss = readFileSync(
      join(here, "../../tv-dashboard-presentation/src/native-screens.css"),
      "utf8",
    );

    const canvasBody = ruleBody(editorCss, ".dashboard-tv-dashboard .td-composer__canvas");
    expect(canvasBody).toMatch(/^\s*overflow:\s*hidden\s*;/m);
    expect(canvasBody).not.toMatch(/^\s*overflow:\s*visible\s*;/m);

    const comunicadoBody = ruleBody(presentationCss, ".tdp-comunicado");
    expect(comunicadoBody).toMatch(/^\s*overflow:\s*hidden\s*;/m);

    const stageBody = ruleBody(presentationCss, ".tdp-design-viewport__stage");
    expect(stageBody).toMatch(/^\s*overflow:\s*hidden\s*;/m);
  });
});
