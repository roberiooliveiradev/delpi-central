import { describe, expect, it } from "vitest";

import type { KaizenRecord } from "../types/kaizen";
import {
  KAIZEN_PDF_NARRATIVE_MAX_CHARS,
  buildKaizenDelpiDocumentSpec,
  truncateKaizenPdfText,
} from "./kaizenPdfSpec";

function sampleRecord(overrides: Partial<KaizenRecord> = {}): KaizenRecord {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    branch_code: "01",
    title: "Suporte para tablet no carrinho",
    accountable: "Ana Silva",
    sector: "Montagem",
    investment: 450,
    savings_type: "tempo",
    seconds_per_occurrence: 12,
    occurrences_per_day: 80,
    hourly_cost: 45,
    quantity_saved_per_day: null,
    unit_material_cost: null,
    fixed_daily_savings: null,
    daily_savings: 120,
    annual_savings: 30_360,
    realized_daily_savings: 110,
    realized_annual_savings: 27_830,
    status: "implantado",
    date_idea_received: "2026-01-10",
    date_committee_approved: "2026-01-20",
    date_implemented: "2026-02-01",
    date_discontinued: null,
    notes: null,
    process_description: "Operador segurava o tablet com a mão.",
    problem_description: "Perda de tempo e risco de queda.",
    improvement_description: "Suporte fixo no carrinho.",
    expected_result: "Mãos livres e menos paradas.",
    category: "Ergonomia",
    categories: ["Ergonomia", "Produtividade"],
    current_revision_number: 1,
    savings_valid_until: "2027-02-01",
    savings_active: true,
    participants: [
      { name: "Ana Silva", role: "responsavel" },
      { name: "Bruno Costa", role: "participante" },
    ],
    created_at: "2026-01-10T12:00:00Z",
    updated_at: "2026-02-01T12:00:00Z",
    ...overrides,
  };
}

describe("truncateKaizenPdfText", () => {
  it("trunca com reticências", () => {
    expect(truncateKaizenPdfText("abcdefghij", 5)).toBe("abcd…");
  });

  it("usa fallback para vazio", () => {
    expect(truncateKaizenPdfText("  ", 10)).toBe("—");
  });
});

describe("buildKaizenDelpiDocumentSpec", () => {
  it("monta cabeçalho, summary, narrativa e equipe", () => {
    const spec = buildKaizenDelpiDocumentSpec(sampleRecord());

    expect(spec.documentTitle).toBe("Ficha Kaizen");
    expect(spec.subtitle).toBe("Suporte para tablet no carrinho");
    expect(spec.badge).toBe("Implantado");
    expect(spec.badgeTone).toBe("approved");

    const summary = Object.fromEntries((spec.summaryLines ?? []).map((line) => [line.label, line.value]));
    expect(summary.Unidade).toContain("Santa Catarina");
    expect(summary.Setor).toBe("Montagem");
    expect(summary.Categorias).toContain("Ergonomia");
    expect(summary["Tipo de economia"]).toBeTruthy();
    expect(summary["Economia/ano (est.)"]).toBeTruthy();
    expect(summary.Efetividade).toContain("%");
    expect(summary.Implantação).toBe("01/02/2026");

    expect(spec.textSections).toHaveLength(4);
    expect(spec.textSections?.map((item) => item.title)).toEqual([
      "Processo",
      "Problema",
      "Melhoria",
      "Resultado esperado",
    ]);
    expect(spec.textSections?.[0]?.body).toContain("tablet");

    expect(spec.tables?.[0]?.title).toBe("Equipe");
    expect(spec.tables?.[0]?.rows).toHaveLength(2);
  });

  it("marca cancelado como rejected e trunca narrativa longa", () => {
    const long = "x".repeat(KAIZEN_PDF_NARRATIVE_MAX_CHARS + 40);
    const spec = buildKaizenDelpiDocumentSpec(
      sampleRecord({
        status: "cancelado",
        process_description: long,
        participants: [],
      }),
    );

    expect(spec.badge).toBe("Cancelado");
    expect(spec.badgeTone).toBe("rejected");
    expect(spec.textSections?.[0]?.body.endsWith("…")).toBe(true);
    expect(spec.textSections?.[0]?.body.length).toBeLessThanOrEqual(KAIZEN_PDF_NARRATIVE_MAX_CHARS);
    expect(spec.tables).toBeUndefined();
  });
});
