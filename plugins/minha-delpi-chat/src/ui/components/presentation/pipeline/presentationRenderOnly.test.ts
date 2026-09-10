import { describe, expect, it } from "vitest";
import { buildStackSectionChrome } from "./presentationStackSections";
import { routeFraming, routeTitle } from "../../../../content/operationalPresentationContent";

describe("MFE render-only display semantics (E4)", () => {
  it("does not invent domain route titles locally", () => {
    expect(routeTitle("stock")).toBe("Resultado");
    expect(routeTitle("structure")).toBe("Resultado");
    expect(routeTitle("inspection")).toBe("Resultado");
  });

  it("does not invent domain route framing locally", () => {
    expect(routeFraming("stock")).toBe("");
    expect(routeFraming("guide")).toBe("");
  });

  it("renders API section titles for unseen domains without local domain map", () => {
    const chrome = buildStackSectionChrome("guide", {
      guide: "Roteiro customizado da API",
    });
    expect(chrome.title).toBe("Roteiro customizado da API");
  });

  it("falls back to generic Resultado for domain sections without API title", () => {
    expect(buildStackSectionChrome("guide").title).toBe("Resultado");
    expect(buildStackSectionChrome("inspection").title).toBe("Resultado");
    expect(buildStackSectionChrome("structure").title).toBe("Resultado");
  });
});
