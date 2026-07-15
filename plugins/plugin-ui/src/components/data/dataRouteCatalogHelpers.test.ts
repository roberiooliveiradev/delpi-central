import { describe, expect, it } from "vitest";

import {
  formatParamHintLine,
  humanizeMetaShape,
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
});
