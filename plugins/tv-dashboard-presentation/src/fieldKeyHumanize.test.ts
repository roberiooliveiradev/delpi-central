import { describe, expect, it } from "vitest";

import {
  catalogFieldsFromRouteLabels,
  humanizeFieldKey,
  isWeakFieldLabel,
  splitFieldKeyTokens,
} from "./fieldKeyHumanize";

describe("fieldKeyHumanize", () => {
  it("usa rótulo curado por chave completa", () => {
    expect(humanizeFieldKey("gross_savings_month")).toBe("Economia bruta (mês)");
    expect(humanizeFieldKey("month")).toBe("Mês");
    expect(humanizeFieldKey("goal_value")).toBe("Meta cadastrada");
    expect(humanizeFieldKey("comparable_goal")).toBe("Meta do período");
    expect(humanizeFieldKey("reference_goal")).toBe("Meta mês (referência)");
    expect(humanizeFieldKey("solutions_started_in_period_count")).toBe(
      "Soluções iniciadas no período",
    );
  });

  it("traduz tokens com _ como espaço quando não há chave completa", () => {
    expect(humanizeFieldKey("gross_cost_rate")).toBe("Bruto custo taxa");
    expect(humanizeFieldKey("goal_amount")).toBe("Meta valor");
    expect(humanizeFieldKey("unknown_field_xyz")).toBe("Unknown field xyz");
  });

  it("quebra camelCase com espaços (não gruda Valordia)", () => {
    expect(splitFieldKeyTokens("valorDia")).toEqual(["valor", "dia"]);
    expect(humanizeFieldKey("valorDia")).toBe("Valor dia");
    expect(humanizeFieldKey("valor_dia")).toBe("Valor dia");
    expect(humanizeFieldKey("totalQuantidade")).toBe("Total quantidade");
    expect(humanizeFieldKey("total_quantidade")).toBe("Total quantidade");
    expect(humanizeFieldKey("registrosSemCusto")).toBe("Registros sem custo");
    expect(humanizeFieldKey("registros_sem_custo")).toBe("Registros sem custo");
    expect(humanizeFieldKey("totalValor")).toBe("Total valor");
  });

  it("detecta label fraco (chave, underscore→espaço ou grudado)", () => {
    expect(isWeakFieldLabel("gross_savings_month", "gross_savings_month")).toBe(true);
    expect(isWeakFieldLabel("gross_savings_month", "gross savings month")).toBe(true);
    expect(isWeakFieldLabel("gross_savings_month", "Economia bruta (mês)")).toBe(false);
    expect(isWeakFieldLabel("valorDia", "Valordia")).toBe(true);
    expect(isWeakFieldLabel("valor_dia", "Valordia")).toBe(true);
    /* "Valor dia" = tokens espaçados (fallback); curated real permanece forte. */
    expect(isWeakFieldLabel("valorDia", "Valor do dia")).toBe(false);
  });

  it("catálogo ignora rótulo grudado do meta e humaniza", () => {
    const fields = catalogFieldsFromRouteLabels(["valorDia"], {
      valorDia: "Valordia",
    });
    expect(fields[0]?.label).toBe("Valor dia");
  });

  it("catálogo inclui chaves só em valueFieldLabels", () => {
    const fields = catalogFieldsFromRouteLabels(
      ["total_hours_saved_until_now"],
      {
        total_hours_saved_until_now: "Horas economizadas",
        gross_savings_month: "Economia bruta (mês)",
      },
    );
    expect(fields.map((item) => item.field).sort()).toEqual([
      "gross_savings_month",
      "total_hours_saved_until_now",
    ]);
    expect(fields.find((item) => item.field === "gross_savings_month")?.label).toBe(
      "Economia bruta (mês)",
    );
  });
});
