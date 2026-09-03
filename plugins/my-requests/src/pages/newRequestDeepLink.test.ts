import { describe, expect, it } from "vitest";

import { readTypeCodeFromSearch } from "./newRequestDeepLink";

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
