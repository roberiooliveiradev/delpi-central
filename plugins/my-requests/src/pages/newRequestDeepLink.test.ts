import { describe, expect, it } from "vitest";

import { findTypeForDeepLink, readTypeCodeFromSearch } from "./newRequestDeepLink";

describe("readTypeCodeFromSearch", () => {
  it("lê type=", () => {
    expect(readTypeCodeFromSearch("?type=invoice-issuance")).toBe("invoice-issuance");
  });

  it("lê type_code= como alias", () => {
    expect(readTypeCodeFromSearch("type_code=raw-material-creation")).toBe(
      "raw-material-creation",
    );
  });

  it("retorna vazio sem query", () => {
    expect(readTypeCodeFromSearch("")).toBe("");
  });
});

describe("findTypeForDeepLink", () => {
  const types = [
    { code: "invoice-issuance", name: "NF" },
    { code: "raw-material-creation", name: "MP" },
  ];

  it("encontra tipo para abrir o form", () => {
    expect(findTypeForDeepLink(types, "invoice-issuance")?.name).toBe("NF");
  });

  it("retorna null para tipo inválido", () => {
    expect(findTypeForDeepLink(types, "missing")).toBeNull();
    expect(findTypeForDeepLink(types, "")).toBeNull();
  });
});
