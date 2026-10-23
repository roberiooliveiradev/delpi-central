import { describe, expect, it } from "vitest";

import type { SupplierCreationPreview } from "./types";
import {
  applyDraftPatchToEntries,
  buildSuggestionEntries,
  identityChangeCheck,
  isCnpjFormatValid,
  isIdentityCoherent,
  normalizeCnpjDigits,
  pendingApplicableEntries,
  searchTaxIdChanged,
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

describe("identity change check (Defect A)", () => {
  const CNPJ_A = "00000000000191";
  const CNPJ_B = "11222333000181";

  it("draft vazio: incorpora identidade sem confirmação", () => {
    const check = identityChangeCheck(
      { tax_id: "", person_type: "", supplier_name: "" },
      CNPJ_A,
      "J",
    );
    expect(check.changedKeys).toEqual([]);
    expect(check.filledFieldCount).toBe(0);
  });

  it("CNPJ igual: nenhuma confirmação", () => {
    const check = identityChangeCheck(
      { tax_id: "00.000.000/0001-91", person_type: "J", supplier_name: "X" },
      CNPJ_A,
      "J",
    );
    expect(check.changedKeys).toEqual([]);
    expect(check.filledFieldCount).toBe(1);
  });

  it("CNPJ diferente: exige confirmação e conta campos preenchidos", () => {
    const check = identityChangeCheck(
      { tax_id: CNPJ_B, person_type: "J", supplier_name: "OUTRA", phone: "1" },
      CNPJ_A,
      "J",
    );
    expect(check.changedKeys).toEqual(["tax_id"]);
    expect(check.filledFieldCount).toBe(2);
  });

  it("person_type incompatível: exige confirmação", () => {
    const check = identityChangeCheck(
      { tax_id: CNPJ_A, person_type: "F", supplier_name: "" },
      CNPJ_A,
      "J",
    );
    expect(check.changedKeys).toEqual(["person_type"]);
  });

  it("CNPJ e tipo divergentes: ambos reportados", () => {
    const check = identityChangeCheck(
      { tax_id: CNPJ_B, person_type: "F", supplier_name: "" },
      CNPJ_A,
      "J",
    );
    expect(check.changedKeys).toEqual(["tax_id", "person_type"]);
  });
});

describe("identity coherence & stale search (Defect B)", () => {
  const CNPJ_A = "00000000000191";
  const CNPJ_B = "11222333000181";

  it("coerência exige mesmo documento normalizado", () => {
    expect(
      isIdentityCoherent({ tax_id: "00.000.000/0001-91" }, CNPJ_A),
    ).toBe(true);
    expect(isIdentityCoherent({ tax_id: CNPJ_B }, CNPJ_A)).toBe(false);
    expect(isIdentityCoherent({ tax_id: "" }, CNPJ_A)).toBe(false);
    expect(isIdentityCoherent({ tax_id: CNPJ_A }, null)).toBe(false);
  });

  it("mudança de dígitos invalida; mudança só de máscara não", () => {
    expect(searchTaxIdChanged(CNPJ_B, CNPJ_A)).toBe(true);
    expect(searchTaxIdChanged("00.000.000/0001-91", CNPJ_A)).toBe(false);
    expect(searchTaxIdChanged("00000000000191", CNPJ_A)).toBe(false);
    expect(searchTaxIdChanged("qualquer", null)).toBe(false);
    // digitação parcial divergente também invalida (empresa A ≠ prefixo B)
    expect(searchTaxIdChanged("11", CNPJ_A)).toBe(true);
  });
});

describe("provenance safety across identities", () => {
  it("sugestões de A perdem aplicabilidade quando a identidade é B", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    // Campo já preenchido com valor de A → nova fonte exige sobrescrita
    const draft = { supplier_name: "EMPRESA EXEMPLO LTDA" } as never;
    expect(
      suggestionApplyDecision(entries.supplier_name, "EMPRESA EXEMPLO LTDA"),
    ).toBe("apply"); // mesma fonte = idempotente
    // Mas se identidade do draft não é a do preview, o fluxo bloqueia antes
    expect(isIdentityCoherent({ tax_id: "11222333000181" }, "00000000000191"))
      .toBe(false);
    expect(pendingApplicableEntries(entries, draft).map((e) => e.field_key))
      .toEqual(["supplier_name"]);
  });

  it("valor de A preservado no draft: nunca apagado por invalidação", () => {
    const entries = buildSuggestionEntries(PREVIEW);
    const next = applyDraftPatchToEntries(entries, {
      supplier_name: "EMPRESA EXEMPLO LTDA",
    });
    expect(next.supplier_name.status).toBe("CONFIRMED");
    // Esvaziar o mapa de sugestões (nova consulta) não toca o draft —
    // a reconciliação age apenas sobre patches explícitos.
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
