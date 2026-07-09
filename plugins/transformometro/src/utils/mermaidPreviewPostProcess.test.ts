import { describe, expect, it } from "vitest";

import { postProcessMermaidPreviewSvg } from "./mermaidPreviewPostProcess";

describe("postProcessMermaidPreviewSvg", () => {
  it("aplica classe e fundo escuro no svg", () => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg"><rect fill="#ffffff" width="400" height="300"/><g class="cluster"><rect fill="#f1f5f9"/></g></svg>`;
    const processed = postProcessMermaidPreviewSvg(svg, true);

    expect(processed).toContain('class="tm-mermaid-svg tm-mermaid-svg--dark"');
    expect(processed).toContain('fill="#111827"');
    expect(processed).toContain("background-color: #111827");
  });
});
