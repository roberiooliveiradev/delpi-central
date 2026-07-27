import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Pasteboard: marquee/desenho no zoom-sizer (gutter), não só no retângulo do slide.
 */
describe("pasteboard interaction contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const composer = readFileSync(join(base, "../components/ComunicadoComposer.tsx"), "utf8");

  it("pointerdown de marquee/desenho está no zoom-sizer (container externo)", () => {
    expect(composer).toMatch(
      /className="td-composer__canvas-zoom-sizer"[\s\S]*?onPointerDown=\{handleCanvasPointerDown\}/,
    );
    /* Slide não deve ser o único hit target do gesto de fundo. */
    const canvasBlock = composer.slice(
      composer.indexOf('data-viewport={viewportProfile'),
      composer.indexOf("td-composer__stage"),
    );
    expect(canvasBlock).not.toMatch(/onPointerDown=\{handleCanvasPointerDown\}/);
  });
});
