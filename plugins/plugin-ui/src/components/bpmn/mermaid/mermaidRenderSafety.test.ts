import { describe, expect, it } from "vitest";

import {
  cleanupMermaidRenderArtifacts,
  isMermaidErrorSvg,
  sanitizeMermaidRenderId,
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
