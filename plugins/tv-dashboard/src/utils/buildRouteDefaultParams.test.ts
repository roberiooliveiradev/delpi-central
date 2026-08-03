import { describe, expect, it } from "vitest";

import { buildRouteDefaultParams, CONVENIENT_REQUIRED_DEFAULTS } from "./buildRouteDefaultParams";

describe("buildRouteDefaultParams", () => {
  it("aplica schema.default e filial (sem periodDays nem dateRangePreset no bloco)", () => {
    const params = buildRouteDefaultParams({
      operationId: "get_retrabalhos_resumo",
      label: "Retrabalhos",
      category: "quality",
      defaultParams: { periodDays: 30 },
      paramSchema: {
        filial: { type: "string", optional: false },
        dataInicio: { type: "string", optional: true },
        dataFim: { type: "string", optional: true },
        granularity: { type: "string", optional: false, default: "day" },
      },
    });
    expect(params.filial).toBe(CONVENIENT_REQUIRED_DEFAULTS.filial);
    expect(params.periodDays).toBeUndefined();
    expect(params.granularity).toBe("day");
    // Herda Programação/slide — não sombreia dataDefaults.
    expect(params.dateRangePreset).toBeUndefined();
  });

  it("usa filial SC em rotas de agendamento sem preset de período no bloco", () => {
    const params = buildRouteDefaultParams({
      operationId: "list_bookings_scheduling_bookings_get",
      label: "Reservas",
      category: "scheduling",
      path: "/scheduling/bookings",
      paramSchema: {
        branch: { type: "string", optional: false },
        from: { type: "string", optional: false },
        to: { type: "string", optional: false },
      },
    });
    expect(params.branch).toBe("SC");
    expect(params.dateRangePreset).toBeUndefined();
  });

  it("preenche department_id obrigatório do IDD", () => {
    const params = buildRouteDefaultParams({
      operationId: "get_dashboard_department_idd",
      label: "IDD",
      category: "system",
      path: "/dashboard/department-idd",
      paramSchema: {
        department_id: { type: "string", optional: false },
      },
    });
    expect(params.department_id).toBe("commercial");
  });

  it("SI com competence + datas não grava dateRangePreset no bloco (herança)", () => {
    const params = buildRouteDefaultParams({
      operationId: "get_si_indicator_quality_ppm_external_realized",
      label: "PPM Externo — realizado",
      category: "quality",
      path: "/dashboard/indicators/quality-ppm-external/realized",
      paramStrategy: "date_range",
      paramSchema: {
        competence: { type: "string", optional: true, label: "Competência" },
        start_date: { type: "string", optional: true, label: "Data início" },
        end_date: { type: "string", optional: true, label: "Data fim" },
        branch: { type: "string", optional: true, label: "Filial" },
      },
    });
    expect(params.dateRangePreset).toBeUndefined();
    expect(params.branch).toBeUndefined();
  });

  it("rota openEndedDateRange usa Personalizado sem periodDays (histórico completo)", () => {
    const params = buildRouteDefaultParams({
      operationId: "get_transformometro_savings_investment_series",
      label: "Economia bruta vs Investimento",
      category: "engineering",
      openEndedDateRange: true,
      defaultParams: { periodDays: 30 },
      paramSchema: {
        start_date: { type: "string", optional: true },
        end_date: { type: "string", optional: true },
        granularity: { type: "string", optional: true, default: "month" },
      },
    });
    expect(params.dateRangePreset).toBe("custom");
    expect(params.periodDays).toBeUndefined();
    expect(params.granularity).toBe("month");
  });
});
