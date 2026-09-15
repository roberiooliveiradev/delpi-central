import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const cssPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../index.css");
const css = readFileSync(cssPath, "utf8");

/**
 * Regressão: barra de controles em flex no editor encolhia o `<video>` vs
 * apresentação (controles em overlay absoluto → vídeo 100% do frame).
 */
describe("editor video size parity contract", () => {
  it("não usa flex-column no bloco de vídeo do composer", () => {
    const block = css.match(
      /\.dashboard-tv-dashboard \.td-composer__media-block--video\{[^}]+\}/,
    )?.[0];
    expect(block).toBeTruthy();
    expect(block).not.toMatch(/flex-direction\s*:\s*column/);
    expect(block).toMatch(/display\s*:\s*block/);
  });

  it("ancora o preview de vídeo em absolute fill", () => {
    const preview = css.match(
      /\.dashboard-tv-dashboard \.td-composer__media-block--video \.td-composer__media-preview\{[^}]+\}/,
    )?.[0];
    expect(preview).toBeTruthy();
    expect(preview).toMatch(/position\s*:\s*absolute/);
    expect(preview).toMatch(/inset\s*:\s*0/);
    expect(preview).not.toMatch(/flex\s*:/);
  });

  it("mantém controles do editor como overlay absoluto", () => {
    const controls = css.match(
      /\.dashboard-tv-dashboard \.td-composer__video-controls\{[^}]+\}/,
    )?.[0];
    expect(controls).toBeTruthy();
    expect(controls).toMatch(/position\s*:\s*absolute/);
    expect(controls).toMatch(/bottom\s*:\s*0/);
    expect(controls).not.toMatch(/flex-shrink\s*:\s*0/);
  });
});
