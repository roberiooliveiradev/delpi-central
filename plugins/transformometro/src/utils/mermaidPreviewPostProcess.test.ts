import { describe, expect, it } from "vitest";

import { postProcessMermaidPreviewSvg } from "./mermaidPreviewPostProcess";

describe("postProcessMermaidPreviewSvg", () => {
  it("aplica classe e fundo escuro no svg", () => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect fill="#ffffff" width="400" height="300"/><g class="cluster"><rect fill="#f1f5f9"/></g></svg>`;
    const processed = postProcessMermaidPreviewSvg(svg, true);

    expect(processed).toContain('class="tm-mermaid-svg tm-mermaid-svg--dark"');
    expect(processed).toContain('tm-mermaid-canvas-bg');
    expect(processed).toContain('fill="#111827"');
    expect(processed).toContain("background-color:#111827");
  });

  it("normaliza fill claro em style inline", () => {
    const svg = `<svg viewBox="0 0 200 100"><rect style="fill:#ffffff;stroke:none" width="200" height="100"/></svg>`;
    const processed = postProcessMermaidPreviewSvg(svg, true);

    expect(processed).toContain('fill="#111827"');
    expect(processed).not.toContain("#ffffff");
    expect(processed).not.toContain("fill:#ffffff");
  });

  it("corrige estilo embutido do mermaid com seletor por id", () => {
    const svg = [
      '<svg id="mermaid-1" viewBox="0 0 320 180">',
      "<style>#mermaid-1 .background { fill: #ffffff; }</style>",
      '<rect class="background" width="320" height="180"/>',
      "</svg>",
    ].join("");
    const processed = postProcessMermaidPreviewSvg(svg, true);

    expect(processed).toContain("fill: #111827");
    expect(processed).toContain('data-tm="tm-mermaid-theme-overrides"');
    expect(processed).not.toContain("fill: #ffffff");
  });

  it("normaliza fundo claro em hex curto (#ffff)", () => {
    const svg = `<svg viewBox="0 0 100 80"><rect fill="#ffff" width="100" height="80"/></svg>`;
    const processed = postProcessMermaidPreviewSvg(svg, true);

    expect(processed).toContain('fill="#111827"');
    expect(processed).not.toContain("#ffff");
  });
});
