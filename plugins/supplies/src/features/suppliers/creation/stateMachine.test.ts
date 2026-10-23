import { describe, expect, it } from "vitest";

import type { SupplierCreationPreview } from "./types";
import {
  applyDraftPatchToEntries,
  buildSuggestionEntries,
  isCnpjFormatValid,
  normalizeCnpjDigits,
  pendingApplicableEntries,
  suggestionApplyDecision,
} from "./stateMachine";

const PREVIEW: SupplierCreationPreview = {
  tax_id_masked: "00.***.***/0001-**",
  person_type: "J",
  duplicate_check: { status: "CLEAR", matches: [] },
  suggestions: [
    {
      field_key: "supplier_name",
      suggested_value: "EMPRESA EXEMPLO LTDA",
      source: {
        provider_id: "brasilapi-cnpj-v1",
        retrieved_at: "2026-10-23T12:00:00Z",
      },
      applicable: true,
    },
    {
      field_key: "supplier_short_name",
      suggested_value: "EXEMPLO",
      source: {
        provider_id: "brasilapi-cnpj-v1",
        retrieved_at: "2026-10-23T12:00:00Z",
      },
      applicable: false,
    },
  ],
  unavailable_fields: ["payment_condition_code"],
  write_enabled: false,
};

describe("cnpj format", () => {
  it("accepts valid CNPJs", () => {
    expect(isCnpjFormatValid("00000000000191")).toBe(true);
    expect(isCnpjFormatValid("11222333000181")).toBe(true);
  });

  it("accepts masked input", () => {
    expect(normalizeCnpjDigits("00.000.000/0001-91")).toBe("00000000000191");
    expect(isCnpjFormatValid("00.000.000/0001-91")).toBe(true);
  });

  it("rejects invalid check digits and shapes", () => {
    expect(isCnpjFormatValid("00000000000192")).toBe(false);
    expect(isCnpjFormatValid("123")).toBe(false);
    expect(isCnpjFormatValid("11111111111111")).toBe(false);
    expect(isCnpjFormatValid("")).toBe(false);
  });
});

describe("suggestion entries", () => {
  it("maps suggestions to SUGGESTED and unavailable to UNAVAILABLE", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    expect(entries.supplier_name.status).toBe("SUGGESTED");
    expect(entries.supplier_name.applicable).toBe(true);
    expect(entries.supplier_short_name.applicable).toBe(false);
    expect(entries.payment_condition_code.status).toBe("UNAVAILABLE");
    expect(entries.payment_condition_code.suggested_value).toBeNull();
  });

  it("never invents suggestions for unmapped fields", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    expect(entries.email).toBeUndefined();
    expect(entries.tax_id).toBeUndefined();
  });
});

describe("apply decision", () => {
  const entries = buildSuggestionEntries(PREVIEW);

  it("empty field applies", () => {
    expect(
      suggestionApplyDecision(entries.supplier_name, ""),
    ).toBe("apply");
  });

  it("same value applies idempotently", () => {
    expect(
      suggestionApplyDecision(entries.supplier_name, "EMPRESA EXEMPLO LTDA"),
    ).toBe("apply");
  });

  it("edited field requires explicit overwrite confirmation", () => {
    expect(
      suggestionApplyDecision(entries.supplier_name, "OUTRO NOME"),
    ).toBe("confirm_overwrite");
  });

  it("non-applicable suggestion is blocked", () => {
    expect(
      suggestionApplyDecision(entries.supplier_short_name, ""),
    ).toBe("blocked");
  });

  it("unavailable field is blocked", () => {
    expect(
      suggestionApplyDecision(entries.payment_condition_code, ""),
    ).toBe("blocked");
  });
});

describe("draft patch reconciliation", () => {
  it("marks applied suggestion as CONFIRMED", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    const next = applyDraftPatchToEntries(entries, {
      supplier_name: "EMPRESA EXEMPLO LTDA",
    });
    expect(next.supplier_name.status).toBe("CONFIRMED");
  });

  it("marks divergent edit as MANUALLY_CHANGED", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    const next = applyDraftPatchToEntries(entries, {
      supplier_name: "NOME DIGITADO",
    });
    expect(next.supplier_name.status).toBe("MANUALLY_CHANGED");
  });

  it("cleared field returns to SUGGESTED", () => {
    const applied = applyDraftPatchToEntries(buildSuggestionEntries(PREVIEW), {
      supplier_name: "EMPRESA EXEMPLO LTDA",
    });
    const next = applyDraftPatchToEntries(applied, { supplier_name: "" });
    expect(next.supplier_name.status).toBe("SUGGESTED");
  });

  it("unrelated edits keep the map referentially equal", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    expect(
      applyDraftPatchToEntries(entries, { phone: "4733330000" }),
    ).toBe(entries);
  });
});

describe("pending applicable", () => {
  it("lists only eligible empty-field suggestions", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    const pending = pendingApplicableEntries(entries, {
      supplier_name: "",
    } as never);
    expect(pending.map((e) => e.field_key)).toEqual(["supplier_name"]);
    // short_name é não-elegível; unavailable nunca entra
  });

  it("excludes fields already filled differently", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    const pending = pendingApplicableEntries(entries, {
      supplier_name: "DIGITADO",
    } as never);
    expect(pending).toHaveLength(0);
  });
});
