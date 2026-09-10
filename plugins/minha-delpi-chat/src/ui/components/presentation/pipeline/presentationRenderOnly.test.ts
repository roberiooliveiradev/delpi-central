import { describe, expect, it } from "vitest";
import productOperationalContent from "../../../../content/product_operational_content.json";
import { routeFraming, routeTitle } from "../../../../content/operationalPresentationContent";
import { buildStackSectionChrome } from "./presentationStackSections";

describe("MFE render-only display semantics (E4/E13)", () => {
  it("does not invent domain route titles locally", () => {
    expect(routeTitle("stock")).toBe("Resultado");
    expect(routeTitle("structure")).toBe("Resultado");
    expect(routeTitle("inspection")).toBe("Resultado");
  });

  it("does not invent domain route framing locally", () => {
    expect(routeFraming("stock")).toBe("");
    expect(routeFraming("guide")).toBe("");
  });

  it("does not keep routeTitles/routeFraming mirrors in local JSON", () => {
    const presentation = productOperationalContent.presentation as Record<string, unknown>;
    expect(presentation.routeTitles).toBeUndefined();
    expect(presentation.routeFraming).toBeUndefined();
  });

  it("keeps scopes.byPathFragment synced with API intent (open-orders present)", () => {
    expect(productOperationalContent.scopes.byPathFragment["/open-orders"]).toBe(
      "pedidos em aberto",
    );
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
