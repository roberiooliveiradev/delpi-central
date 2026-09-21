import { describe, expect, it } from "vitest";

import {
  CONSOLIDATED_UNIT_CONTEXT,
  buildDashboardKpiContextLabel,
  formatDashboardPeriodLabel,
} from "./dashboardKpiContext";

const filiais = [
  { id: "01", label: "Santa Catarina", codigo_filial: "01" },
  { id: "02", label: "Espírito Santo", codigo_filial: "02" },
];
const setores = [{ id: "dep-1", label: "Qualidade", filiais: ["01"] }];
const period = "01/09/2026 — 21/09/2026";

describe("dashboardKpiContext", () => {
  it("formata o período em pt-BR", () => {
    expect(formatDashboardPeriodLabel("2026-09-01", "2026-09-21")).toBe(period);
  });

  it("identifica consolidado sem tratar unidade como autorização", () => {
    expect(
      buildDashboardKpiContextLabel({
        viewMode: "consolidated",
        filialIds: [],
        periodLabel: period,
        filiais,
      }),
    ).toBe(`${CONSOLIDATED_UNIT_CONTEXT} · ${period}`);
  });

  it("usa o nome canônico da unidade", () => {
    expect(
      buildDashboardKpiContextLabel({
        viewMode: "filial",
        filialIds: ["01"],
        periodLabel: period,
        filiais,
      }),
    ).toBe(`Santa Catarina · ${period}`);
  });

  it("identifica departamento e unidade", () => {
    expect(
      buildDashboardKpiContextLabel({
        viewMode: "department",
        filialIds: ["01"],
        setorIds: ["dep-1"],
        periodLabel: period,
        filiais,
        setores,
      }),
    ).toBe(`Qualidade · Santa Catarina · ${period}`);
  });

  it("não inventa rótulo quando o nome canônico falta", () => {
    expect(
      buildDashboardKpiContextLabel({
        viewMode: "filial",
        filialIds: ["xyz"],
        periodLabel: period,
        filiais,
      }),
    ).toBe(`xyz · ${period}`);
  });
});
