import { describe, expect, it } from "vitest";

import { enumOptionLabel, resolveParamSelectOptions, visibleParamSchema } from "./DataParamFields";

describe("resolveParamSelectOptions", () => {
  it("usa enum do schema com labels PT", () => {
    expect(resolveParamSelectOptions("granularity", { enum: ["day", "week"] })).toEqual([
      { value: "day", label: "Dia" },
      { value: "week", label: "Semana" },
    ]);
  });

  it("converte boolean em Sim/Não", () => {
    expect(resolveParamSelectOptions("legacy", { type: "boolean" })).toEqual([
      { value: "true", label: "Sim" },
      { value: "false", label: "Não" },
    ]);
  });

  it("mantém periodDays como input numérico (sem select)", () => {
    expect(resolveParamSelectOptions("periodDays", { type: "integer" })).toBeNull();
  });

  it("retorna null para texto livre", () => {
    expect(resolveParamSelectOptions("product_code", { type: "string" })).toBeNull();
  });
});

describe("enumOptionLabel", () => {
  it("mapeia customer_segment", () => {
    expect(enumOptionLabel("customer_segment", "new_business")).toBe("Novos negócios");
  });
});

describe("visibleParamSchema", () => {
  it("remove parâmetros fixos do catálogo", () => {
    expect(
      visibleParamSchema(
        {
          periodDays: { type: "integer" },
          granularity: { type: "string", enum: ["day"] },
        },
        { granularity: "day" },
      ),
    ).toEqual({ periodDays: { type: "integer" } });
  });
});
