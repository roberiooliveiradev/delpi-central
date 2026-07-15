import { describe, expect, it } from "vitest";

import { SCRAP_HELP_TOOLTIPS } from "./helpTooltips";

describe("SCRAP_HELP_TOOLTIPS", () => {
  it("expõe textos não vazios para KPIs principais", () => {
    expect(SCRAP_HELP_TOOLTIPS.kpis.valorMes.length).toBeGreaterThan(20);
    expect(SCRAP_HELP_TOOLTIPS.kpis.valorDia.length).toBeGreaterThan(10);
    expect(SCRAP_HELP_TOOLTIPS.kpis.totalPeriodo.length).toBeGreaterThan(10);
  });

  it("cobre filtros, charts, tabela e paginação", () => {
    expect(Object.keys(SCRAP_HELP_TOOLTIPS.filters).length).toBeGreaterThanOrEqual(6);
    expect(Object.keys(SCRAP_HELP_TOOLTIPS.charts).length).toBe(5);
    expect(SCRAP_HELP_TOOLTIPS.table.section.length).toBeGreaterThan(10);
    expect(SCRAP_HELP_TOOLTIPS.pagination.pageSize.length).toBeGreaterThan(5);
  });
});
