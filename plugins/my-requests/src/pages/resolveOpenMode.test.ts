import { describe, expect, it } from "vitest";

import { isInvoiceIssuanceSpecialized, resolveOpenMode } from "./resolveOpenMode";
import type { RequestTypeSummary } from "../types/requests";

function typeStub(
  partial: Pick<RequestTypeSummary, "code" | "name"> &
    Partial<Pick<RequestTypeSummary, "presentation_mode">>,
): RequestTypeSummary {
  return {
    id: partial.code,
    active: true,
    ...partial,
  };
}

describe("resolveOpenMode", () => {
  it("abre specialized / schema_driven / generic por presentation_mode", () => {
    expect(
      resolveOpenMode(
        typeStub({
          code: "invoice-issuance",
          name: "NF",
          presentation_mode: "specialized",
        }),
      ),
    ).toBe("specialized");
    expect(
      resolveOpenMode(
        typeStub({
          code: "raw-material-creation",
          name: "MP",
          presentation_mode: "schema_driven",
        }),
      ),
    ).toBe("schema_driven");
    expect(
      resolveOpenMode(
        typeStub({ code: "other", name: "Outro", presentation_mode: "generic" }),
      ),
    ).toBe("generic");
  });

  it("não força specialized só pelo code", () => {
    expect(
      resolveOpenMode(
        typeStub({
          code: "invoice-issuance",
          name: "NF",
          presentation_mode: "schema_driven",
        }),
      ),
    ).toBe("schema_driven");
  });

  it("reconhece wizard NF só com specialized + code", () => {
    expect(
      isInvoiceIssuanceSpecialized(
        typeStub({
          code: "invoice-issuance",
          name: "NF",
          presentation_mode: "specialized",
        }),
      ),
    ).toBe(true);
    expect(
      isInvoiceIssuanceSpecialized(
        typeStub({
          code: "other-specialized",
          name: "X",
          presentation_mode: "specialized",
        }),
      ),
    ).toBe(false);
  });
});
