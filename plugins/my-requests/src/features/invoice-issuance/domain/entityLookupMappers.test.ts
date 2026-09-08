import { describe, expect, it } from "vitest";

import {
  carrierEntityId,
  carrierToOption,
  partyEntityId,
  partyToOption,
  productEntityId,
  productToOption,
} from "./entityLookupMappers";

describe("entityLookupMappers", () => {
  it("mapeia party com id estável code|store", () => {
    const party = {
      party_type: "customer" as const,
      party_code: "001",
      party_store: "01",
      party_name: "ACME Indústria",
      tax_id: "123",
      blocked: false,
    };
    expect(partyEntityId(party)).toBe("001|01");
    expect(partyToOption(party)).toEqual({
      id: "001|01",
      label: "ACME Indústria",
      secondary: "123 · 001/01",
    });
  });

  it("prioriza CNPJ formatado no secondary do party", () => {
    const party = {
      party_type: "customer" as const,
      party_code: "000001",
      party_store: "06",
      party_name: "WEG AMAZONIA SA",
      tax_id: "84499477000606",
      blocked: false,
    };
    expect(partyToOption(party).secondary).toBe(
      "84.499.477/0006-06 · 000001/06",
    );
  });

  it("mapeia product com id = code", () => {
    const product = {
      code: "P1",
      description: "Produto A",
      unit: "UN",
      blocked: false,
    };
    expect(productEntityId(product)).toBe("P1");
    expect(productToOption(product)).toEqual({
      id: "P1",
      label: "Produto A",
      secondary: "P1",
    });
  });

  it("mapeia carrier com id = carrier_code", () => {
    const carrier = {
      carrier_code: "T01",
      carrier_name: "Rapidão",
      legal_name: null,
      tax_id: null,
      blocked: false,
    };
    expect(carrierEntityId(carrier)).toBe("T01");
    expect(carrierToOption(carrier)).toEqual({
      id: "T01",
      label: "Rapidão",
      secondary: "T01",
    });
  });
});
