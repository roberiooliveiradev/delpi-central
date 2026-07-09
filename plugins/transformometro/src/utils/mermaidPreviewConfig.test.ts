import { describe, expect, it } from "vitest";

import { buildMermaidPreviewConfig, MERMAID_LABEL_WRAPPING_WIDTH } from "./mermaidPreviewConfig";

describe("buildMermaidPreviewConfig", () => {
  it("habilita htmlLabels e quebra de linha no preview", () => {
    const config = buildMermaidPreviewConfig(true);
    expect(config.securityLevel).toBe("sandbox");
    expect(config.htmlLabels).toBe(true);
    expect(config.flowchart).toMatchObject({
      wrappingWidth: MERMAID_LABEL_WRAPPING_WIDTH,
      useMaxWidth: false,
    });
    expect(config.theme).toBe("dark");
  });

  it("usa tema claro quando solicitado", () => {
    expect(buildMermaidPreviewConfig(false).theme).toBe("neutral");
  });
});
