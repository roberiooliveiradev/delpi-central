import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Guias do palco não podem competir com `style.zIndex` dos blocos.
 * Conteúdo fica em `.td-composer__stage-content` (stacking context);
 * guias/smart-guides são irmãos com z-index maior.
 */
describe("stage guides stacking contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(base, "../index.css"), "utf8");
  const composer = readFileSync(join(base, "../components/ComunicadoComposer.tsx"), "utf8");

  it("isola blocos em stage-content e renderiza guias como irmãos", () => {
    expect(composer).toMatch(/className="td-composer__stage-content"/);
    expect(composer).toMatch(/td-composer__stage-guide/);
    const contentIdx = composer.indexOf('className="td-composer__stage-content"');
    const guideIdx = composer.indexOf("td-composer__stage-guide td-composer__stage-guide--v");
    expect(contentIdx).toBeGreaterThan(-1);
    expect(guideIdx).toBeGreaterThan(contentIdx);
  });

  it("CSS: stage-content cria stacking context abaixo das guias", () => {
    expect(css).toMatch(
      /\.td-composer__stage-content\s*\{[^}]*z-index:\s*1/s,
    );
    expect(css).toMatch(
      /\.td-composer__stage-guide\s*\{[^}]*z-index:\s*3/s,
    );
    expect(css).toMatch(
      /\.td-composer__smart-guide\s*\{[^}]*z-index:\s*4/s,
    );
  });
});
