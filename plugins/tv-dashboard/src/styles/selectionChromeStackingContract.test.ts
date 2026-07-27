import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Chrome de seleção (handles) não pode ficar sob blocos vizinhos —
 * e o conteúdo do selecionado não pode subir acima do z do modelo.
 *
 * Overlay `.td-composer__block-chrome` + resolveSelectionChromeOverlayZIndex;
 * wrap usa só resolveBlockWrapStackZIndex (modelo).
 */
describe("selection chrome stacking contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(base, "../index.css"), "utf8");
  const composer = readFileSync(join(base, "../components/ComunicadoComposer.tsx"), "utf8");
  const util = readFileSync(join(base, "../utils/resolveBlockWrapStackZIndex.ts"), "utf8");
  const overlay = readFileSync(
    join(base, "../components/BlockSelectionChromeOverlay.tsx"),
    "utf8",
  );

  it("composer usa overlay de chrome e wrap só com z do modelo", () => {
    expect(composer).toMatch(/BlockSelectionChromeOverlay/);
    expect(composer).toMatch(/resolveBlockWrapStackZIndex\(\{\s*modelZIndex:/);
    expect(composer).not.toMatch(/selectionChromeVisible:/);
    expect(overlay).toMatch(/resolveSelectionChromeOverlayZIndex/);
  });

  it("floor de overlay documentado; group-chrome acima; wrap sem outline de seleção", () => {
    expect(util).toMatch(/SELECTION_CHROME_STACK_FLOOR\s*=\s*10_000/);
    expect(util).toMatch(/resolveSelectionChromeOverlayZIndex/);
    expect(css).toMatch(/\.td-composer__block-chrome\s*\{/);
    expect(css).toMatch(
      /\.td-composer__group-chrome\s*\{[^}]*z-index:\s*13000/s,
    );
    const wrapSelected = css.match(
      /\.td-composer__block-wrap--selected\s*\{([^}]*)\}/,
    )?.[1];
    expect(wrapSelected ?? "").not.toMatch(/outline:/);
  });
});
