import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const stylesRoot = join(here, "../../../styles/bpmn");

describe("diagram viewport CSS contract", () => {
  it("mantém o canvas default como janela com overflow hidden", () => {
    const css = readFileSync(join(stylesRoot, "editor.css"), "utf8");
    expect(css).toContain("overflow: hidden");
    expect(css).toContain("max-height: min(780px, 78vh)");
    expect(css).not.toMatch(/min-height:\s*680px;/);
  });

  it("em fill/fullscreen o canvas ocupa a altura restante sem max-height de janela", () => {
    const css = readFileSync(join(stylesRoot, "editor.css"), "utf8");
    const fillBlock = css.match(
      /delpi-ui-bpmn-editor--fill \.delpi-ui-bpmn-editor__canvas,[\s\S]*?max-height:\s*none/
    );
    expect(fillBlock?.[0]).toMatch(/flex:\s*1 1 0/);
    expect(fillBlock?.[0]).toMatch(/min-height:\s*0/);
  });

  it("não escala o SVG Mermaid com max-width 100% fora do viewport", () => {
    const css = readFileSync(join(stylesRoot, "mermaid.css"), "utf8");
    expect(css).toMatch(/delpi-ui-bpmn-svg-viewport/);
    expect(css).toMatch(/max-width:\s*none;/);
    expect(css).not.toMatch(/\.delpi-ui-bpmn-mermaid svg\{[^}]*max-width:\s*100%/);
  });

  it("preserva fullscreen do workspace como janela e ocupa a altura restante", () => {
    const css = readFileSync(join(stylesRoot, "fullscreen.css"), "utf8");
    expect(css).toMatch(/delpi-ui-bpmn-workspace--fullscreen[\s\S]*overflow:\s*hidden/);
    expect(css).not.toMatch(/min-height:\s*min\(72vh,\s*900px\)/);
    expect(css).toMatch(/workspace--modal-body\{[\s\S]*?flex:\s*1 1 0/);
  });

  it("overlay-tools define altura especificada para o React Flow não colapsar a 0", () => {
    const css = readFileSync(join(stylesRoot, "editor.css"), "utf8");
    const overlayBlock = css.match(
      /editor--overlay-tools \.delpi-ui-bpmn-editor__canvas,[\s\S]*?overflow:\s*hidden;/
    );
    expect(overlayBlock?.[0]).toMatch(/height:\s*min\(680px,\s*70vh\)/);
    expect(overlayBlock?.[0]).not.toMatch(/height:\s*100%;/);
  });
});
