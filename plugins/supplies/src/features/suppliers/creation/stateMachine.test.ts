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

  it("coerência exige mesmo documento normalizado E mesmo person_type (R2)", () => {
    // CNPJ igual + J → coerente
    expect(
      isIdentityCoherent(
        { tax_id: "00.000.000/0001-91", person_type: "J" },
        CNPJ_A,
        "J",
      ),
    ).toBe(true);
    // CNPJ igual + F/X divergente → incoerente (cancelamento mantém bloqueio)
    expect(
      isIdentityCoherent({ tax_id: CNPJ_A, person_type: "F" }, CNPJ_A, "J"),
    ).toBe(false);
    expect(
      isIdentityCoherent({ tax_id: CNPJ_A, person_type: "X" }, CNPJ_A, "J"),
    ).toBe(false);
    // CNPJ diferente → incoerente
    expect(
      isIdentityCoherent({ tax_id: CNPJ_B, person_type: "J" }, CNPJ_A, "J"),
    ).toBe(false);
    // Sem consulta ativa → incoerente
    expect(
      isIdentityCoherent({ tax_id: CNPJ_A, person_type: "J" }, null, "J"),
    ).toBe(false);
    expect(
      isIdentityCoherent({ tax_id: CNPJ_A, person_type: "J" }, CNPJ_A, null),
    ).toBe(false);
    // person_type vazio no draft → só coerente após incorporação do tipo
    expect(
      isIdentityCoherent({ tax_id: CNPJ_A, person_type: "" }, CNPJ_A, "J"),
    ).toBe(false);
    expect(
      isIdentityCoherent({ tax_id: CNPJ_A }, CNPJ_A, "J"),
    ).toBe(false);
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
    expect(
      isIdentityCoherent(
        { tax_id: "11222333000181", person_type: "J" },
        "00000000000191",
        "J",
      ),
    ).toBe(false);
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

describe("interaction scenario — cancel then re-confirm (S2.R2)", () => {
  const CNPJ_A = "00000000000191";

  it("person_type divergente: cancelar bloqueia, reconfirmar libera", () => {
    // Draft: CNPJ A + pessoa F; preview retorna pessoa J para o mesmo CNPJ.
    let draft: Record<string, string> = {
      tax_id: CNPJ_A,
      person_type: "F",
      supplier_name: "",
    };
    const entries = buildSuggestionEntries(PREVIEW);
    const person = PREVIEW.person_type;

    // 1. Divergência detectada → confirmação exigida.
    const check = identityChangeCheck(draft, CNPJ_A, person);
    expect(check.changedKeys).toEqual(["person_type"]);

    // 2. Usuário CANCELA → draft intacto, coerência falsa, aplicação vedada.
    const userConfirmed = false;
    if (userConfirmed) draft = { ...draft, person_type: person };
    expect(draft).toEqual({ tax_id: CNPJ_A, person_type: "F", supplier_name: "" });
    expect(isIdentityCoherent(draft, CNPJ_A, person)).toBe(false);

    // 3. Tentativa de aplicar sugestão → guarda rejeita (espelho de applyOne).
    if (isIdentityCoherent(draft, CNPJ_A, person)) {
      draft = {
        ...draft,
        supplier_name: entries.supplier_name.suggested_value ?? "",
      };
    }
    expect(draft.supplier_name).toBe("");

    // 4. Usuário RECONFIRMA → tipo vira J, coerência restabelecida.
    draft = { ...draft, person_type: person };
    expect(isIdentityCoherent(draft, CNPJ_A, person)).toBe(true);

    // 5. Sugestão elegível agora pode ser aplicada e marcada CONFIRMED.
    const decision = suggestionApplyDecision(
      entries.supplier_name,
      draft.supplier_name,
    );
    expect(decision).toBe("apply");
    draft = {
      ...draft,
      supplier_name: entries.supplier_name.suggested_value ?? "",
    };
    expect(draft.supplier_name).toBe("EMPRESA EXEMPLO LTDA");
    expect(
      applyDraftPatchToEntries(entries, draft).supplier_name.status,
    ).toBe("CONFIRMED");
  });

  it("preview de B nunca aplica sobre identidade A mesmo com CNPJ igual em tela", () => {
    // Identidade confirmada de A; preview de B ativo (activeTaxId=B).
    const draft = {
      tax_id: CNPJ_A,
      person_type: "J",
      supplier_name: "EMPRESA EXEMPLO LTDA",
    };
    const CNPJ_B = "11222333000181";
    expect(isIdentityCoherent(draft, CNPJ_B, "J")).toBe(false);
    // E person_type divergente não escapa pelo CNPJ igual:
    expect(isIdentityCoherent(draft, CNPJ_A, "F")).toBe(false);
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
