import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const stylesRoot = join(here, "../../../styles/bpmn");

describe("diagram viewport CSS contract", () => {
  it("mantém o canvas como janela com overflow hidden", () => {
    const css = readFileSync(join(stylesRoot, "editor.css"), "utf8");
    expect(css).toContain("overflow: hidden");
    expect(css).toContain("max-height: min(780px, 78vh)");
    expect(css).not.toMatch(/min-height:\s*680px;/);
  });

  it("não escala o SVG Mermaid com max-width 100% fora do viewport", () => {
    const css = readFileSync(join(stylesRoot, "mermaid.css"), "utf8");
    expect(css).toMatch(/delpi-ui-bpmn-svg-viewport/);
    expect(css).toMatch(/max-width:\s*none;/);
    expect(css).not.toMatch(/\.delpi-ui-bpmn-mermaid svg\{[^}]*max-width:\s*100%/);
  });

  it("preserva fullscreen do workspace como janela", () => {
    const css = readFileSync(join(stylesRoot, "fullscreen.css"), "utf8");
    expect(css).toMatch(/delpi-ui-bpmn-workspace--fullscreen[\s\S]*overflow:\s*hidden/);
  });
});
