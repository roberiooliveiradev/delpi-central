import { describe, expect, it } from "vitest";

import {
  coerceTestParamValues,
  formatParamHintLine,
  humanizeMetaShape,
  initialTestParamValues,
  missingRequiredTestParams,
  resolveRouteAudienceDescription,
  summarizeRouteParams,
} from "./dataRouteCatalogHelpers";

describe("dataRouteCatalogHelpers", () => {
  it("resume params com labels e obrigatoriedade", () => {
    const params = summarizeRouteParams(
      {
        branch: { label: "Filial", optional: true },
        production_order: { label: "Ordem de produção", optional: false },
        page: { label: "Página", optional: true },
      },
      { page: 1 },
    );
    expect(params.map((p) => p.key)).toEqual(["production_order", "branch"]);
    expect(params[0]?.optional).toBe(false);
    expect(formatParamHintLine(params)).toBe("2 filtros · 1 obrigatório");
  });

  it("humaniza shape e monta descrição de audiência", () => {
    expect(humanizeMetaShape("paged_list")).toBe("Lista / tabela");
    expect(resolveRouteAudienceDescription({ metaShape: "scalar" })).toMatch(/KPI/);
    expect(
      resolveRouteAudienceDescription({
        description: "  Texto de negócio.  ",
        metaShape: "scalar",
      }),
    ).toBe("Texto de negócio.");
    expect(
      resolveRouteAudienceDescription({
        whenToUse: "Use no plantão para OEE.",
        description: "Indicador numérico para «OEE — visão geral».",
        metaShape: "scalar",
      }),
    ).toBe("Use no plantão para OEE.");
    expect(
      resolveRouteAudienceDescription({
        description: "Indicador numérico para «OEE — visão geral».",
        metaShape: "scalar",
      }),
    ).toMatch(/KPI/);
  });

  it("propaga enum e default para o formulário de teste", () => {
    const params = summarizeRouteParams({
      department_id: {
        label: "Departamento",
        optional: false,
        enum: ["commercial", "hr"],
        default: "commercial",
      },
      periodDays: { label: "Dias", type: "integer", optional: true },
    });
    expect(params[0]).toMatchObject({
      key: "department_id",
      enum: ["commercial", "hr"],
      default: "commercial",
    });
    expect(initialTestParamValues(params)).toEqual({ department_id: "commercial" });
    expect(missingRequiredTestParams(params, {})).toHaveLength(1);
    expect(missingRequiredTestParams(params, { department_id: "hr" })).toHaveLength(0);
    expect(
      coerceTestParamValues(params, { department_id: "hr", periodDays: "30" }),
    ).toEqual({
      department_id: "hr",
      periodDays: 30,
    });
  });
});
