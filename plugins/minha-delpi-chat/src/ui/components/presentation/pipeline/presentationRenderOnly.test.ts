import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { routeFraming, routeTitle } from "../../../../content/operationalPresentationContent";
import { buildStackSectionChrome } from "./presentationStackSections";
import { routeKeyFromToolMetadata } from "./presentationMultiRoute";

const contentDir = join(dirname(fileURLToPath(import.meta.url)), "../../../../content");

describe("MFE render-only display semantics (E7.S7)", () => {
  it("does not invent domain route titles locally", () => {
    expect(routeTitle("stock")).toBe("Resultado");
    expect(routeTitle("structure")).toBe("Resultado");
    expect(routeTitle("inspection")).toBe("Resultado");
  });

  it("does not invent domain route framing locally", () => {
    expect(routeFraming("stock")).toBe("");
    expect(routeFraming("guide")).toBe("");
  });

  it("does not keep a mirrored product_operational_content.json in the MFE", () => {
    expect(existsSync(join(contentDir, "product_operational_content.json"))).toBe(false);
  });

  it("prefers API presentationProfileKey over path for route key", () => {
    const key = routeKeyFromToolMetadata({
      path: "/products/10080001/stock",
      presentationProfileKey: "product_structure",
    });
    expect(key).toBe("structure");
  });

  it("negative: unknown path without profileKey stays generic other", () => {
    const key = routeKeyFromToolMetadata({
      path: "/acme/widgets/inventory-v2",
    });
    expect(key).toBe("other");
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
