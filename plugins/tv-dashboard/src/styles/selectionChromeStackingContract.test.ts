import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Chrome de seleção (handles) não pode ficar sob blocos vizinhos.
 * zIndex de paint do wrap selecionado sobe via resolveBlockWrapStackZIndex;
 * group-chrome fica acima do floor de seleção.
 */
describe("selection chrome stacking contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(base, "../index.css"), "utf8");
  const composer = readFileSync(join(base, "../components/ComunicadoComposer.tsx"), "utf8");
  const util = readFileSync(join(base, "../utils/resolveBlockWrapStackZIndex.ts"), "utf8");

  it("composer usa resolveBlockWrapStackZIndex no wrap", () => {
    expect(composer).toMatch(/resolveBlockWrapStackZIndex/);
    expect(composer).toMatch(/selectionChromeVisible:\s*wrapChrome\.showOutline/);
  });

  it("floor de seleção documentado e group-chrome acima dele", () => {
    expect(util).toMatch(/SELECTION_CHROME_STACK_FLOOR\s*=\s*10_000/);
    expect(css).toMatch(
      /\.td-composer__group-chrome\s*\{[^}]*z-index:\s*13000/s,
    );
  });
});
