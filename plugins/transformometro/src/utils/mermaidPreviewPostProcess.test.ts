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

    expect(processed).toContain("fill:#1e293b");
    expect(processed).toContain('fill="#111827"');
    expect(processed).not.toContain("#ffffff");
  });
});
