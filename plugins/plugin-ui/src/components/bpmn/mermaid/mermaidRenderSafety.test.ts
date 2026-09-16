import { describe, expect, it } from "vitest";

import {
  cleanupMermaidRenderArtifacts,
  isMermaidErrorSvg,
  sanitizeMermaidRenderId,
  unwrapMermaidRenderSvg,
} from "./mermaidRenderSafety";

describe("sanitizeMermaidRenderId", () => {
  it("remove dois-pontos do useId do React", () => {
    expect(sanitizeMermaidRenderId("tm-mermaid-:r1:-123")).toBe("tm-mermaid-_r1_-123");
  });

  it("garante id utilizável em seletor CSS", () => {
    expect(sanitizeMermaidRenderId("«bad»")).toBe("bad");
    expect(sanitizeMermaidRenderId("")).toBe("tm_mermaid");
    expect(sanitizeMermaidRenderId("12abc")).toBe("tm_12abc");
  });
});

describe("isMermaidErrorSvg", () => {
  it("detecta SVG de erro padrão do Mermaid", () => {
    expect(
      isMermaidErrorSvg(
        '<svg><text class="error-text">Syntax error in text</text><path class="error-icon"/></svg>',
      ),
    ).toBe(true);
    expect(isMermaidErrorSvg('<svg class="tm-mermaid-svg"><g/></svg>')).toBe(false);
  });

  it("não descarta flowchart válido com error-icon residual", () => {
    const svg =
      '<svg aria-roledescription="flowchart-v2"><g class="node default"></g><g class="node default"></g><path class="error-icon"/></svg>';
    expect(isMermaidErrorSvg(svg)).toBe(false);
  });
});

describe("unwrapMermaidRenderSvg", () => {
  it("extrai o SVG interno do iframe sandbox do Mermaid", () => {
    const inner =
      '<svg width="6166.93" height="14334.83" viewBox="-4 -18 6166.93 14334.83" aria-roledescription="flowchart-v2"><g class="node default"></g></svg>';
    const iframe = `<iframe style="width:100%;height:14334.83px;border:0;margin:0;" src="data:text/html;charset=UTF-8;base64,${btoa(inner)}"></iframe>`;
    const unwrapped = unwrapMermaidRenderSvg(iframe);
    expect(unwrapped.startsWith("<svg")).toBe(true);
    expect(unwrapped).toContain('viewBox="-4 -18 6166.93 14334.83"');
    expect(unwrapped).not.toContain("<iframe");
  });

  it("A/B/C: iframe sandbox → SVG pós-processado preserva world 6166×14334, fit ≠ 135%", async () => {
    const { parseSvgWorldSize, computeFitTransform, DIAGRAM_FIT_MAX_ZOOM, DIAGRAM_ZOOM_MIN } =
      await import("../layout/diagramViewport");
    const { postProcessMermaidPreviewSvg } = await import("./mermaidPreviewPostProcess");
    const inner =
      '<svg width="100%" height="100%" viewBox="-4 -18 6166.93 14334.83" aria-roledescription="flowchart-v2"><g class="node default"></g></svg>';
    const iframe = `<iframe style="width:100%;height:14334.83px" src="data:text/html;charset=UTF-8;base64,${btoa(inner)}"></iframe>`;
    const raw = unwrapMermaidRenderSvg(iframe);
    const processed = postProcessMermaidPreviewSvg(raw, true);
    const world = parseSvgWorldSize(processed);
    expect(world.width).toBeCloseTo(6166.93, 1);
    expect(world.height).toBeCloseTo(14334.83, 1);
    const fit = computeFitTransform(
      { minX: 0, minY: 0, maxX: world.width, maxY: world.height },
      { width: 464, height: 220 }
    );
    expect(fit.zoom).toBe(DIAGRAM_ZOOM_MIN);
    expect(fit.zoom).not.toBe(DIAGRAM_FIT_MAX_ZOOM);
  });
});

describe("cleanupMermaidRenderArtifacts", () => {
  it("remove nós #d{id} e #i{id} do document", () => {
    const id = sanitizeMermaidRenderId("tm-mermaid-r1-1");
    const d = document.createElement("div");
    d.id = `d${id}`;
    d.textContent = "orphan";
    document.body.appendChild(d);
    cleanupMermaidRenderArtifacts(id);
    expect(document.getElementById(`d${id}`)).toBeNull();
  });
});
