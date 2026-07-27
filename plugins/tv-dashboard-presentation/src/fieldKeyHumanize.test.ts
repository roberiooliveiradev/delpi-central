import { describe, expect, it } from "vitest";

import {
  catalogFieldsFromRouteLabels,
  humanizeFieldKey,
  isWeakFieldLabel,
} from "./fieldKeyHumanize";

describe("fieldKeyHumanize", () => {
  it("usa rótulo curado por chave completa", () => {
    expect(humanizeFieldKey("gross_savings_month")).toBe("Economia bruta (mês)");
    expect(humanizeFieldKey("month")).toBe("Mês");
    expect(humanizeFieldKey("solutions_started_in_period_count")).toBe(
      "Soluções iniciadas no período",
    );
  });

  it("traduz tokens com _ como espaço quando não há chave completa", () => {
    expect(humanizeFieldKey("gross_cost_rate")).toBe("Bruto custo taxa");
    expect(humanizeFieldKey("unknown_field_xyz")).toBe("Unknown field xyz");
  });

  it("detecta label fraco (chave ou só underscore→espaço)", () => {
    expect(isWeakFieldLabel("gross_savings_month", "gross_savings_month")).toBe(true);
    expect(isWeakFieldLabel("gross_savings_month", "gross savings month")).toBe(true);
    expect(isWeakFieldLabel("gross_savings_month", "Economia bruta (mês)")).toBe(false);
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
