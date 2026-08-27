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

  it("usa Todas quando o enum de branch inclui Todas", () => {
    const params = buildRouteDefaultParams({
      operationId: "get_inspecoes_entrada_kpi",
      label: "KPI inspeções",
      category: "quality",
      path: "/inspecoes-entrada/kpi",
      paramSchema: {
        branch: { type: "string", optional: false, enum: ["all", "01", "02"] },
      },
    });
    expect(params.branch).toBe("all");
  });
  it("não inventa department_id (usuário escolhe no filtro)", () => {
    const params = buildRouteDefaultParams({
      operationId: "get_dashboard_department_idd",
      label: "IDD",
      category: "system",
      path: "/dashboard/department-idd",
      paramSchema: {
        department_id: {
          type: "string",
          optional: false,
          enum: ["commercial", "quality"],
          default: "commercial",
        },
      },
    });
    expect(params.department_id).toBeUndefined();
  });

  it("select opcional com default de catálogo não é pré-preenchido", () => {
    const params = buildRouteDefaultParams({
      operationId: "list_lmps",
      label: "LMPs",
      category: "quality",
      paramSchema: {
        status: {
          type: "string",
          optional: true,
          enum: ["Todos", "Pontual"],
          default: "Todos",
        },
      },
    });
    expect(params.status).toBeUndefined();
  });

  it("não pré-preenche group_by/granularity opcionais (Não definido aqui)", () => {
    const params = buildRouteDefaultParams({
      operationId: "get_commercial_rol",
      label: "ROL",
      category: "commercial",
      defaultParams: { group_by: "customer" },
      paramSchema: {
        group_by: {
          type: "string",
          optional: true,
          enum: ["none", "customer", "branch"],
          default: "customer",
        },
        granularity: {
          type: "string",
          optional: true,
          enum: ["day", "week", "month", "year"],
          default: "week",
        },
      },
    });
    expect(params.group_by).toBeUndefined();
    expect(params.granularity).toBeUndefined();
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
    // Granularidade opcional: «Não definido aqui» — API aplica default do Query.
    expect(params.granularity).toBeUndefined();
  });

  it("não força bool/int/sort opcionais via defaultParams (todas as rotas)", () => {
    const params = buildRouteDefaultParams({
      operationId: "get_supplies_stock_items",
      label: "Estoque",
      category: "supplies",
      defaultParams: {
        page: 1,
        page_size: 50,
        only_positive: true,
        sort: "stock_value_desc",
      },
      paramSchema: {
        only_positive: { type: "boolean", optional: true, default: true },
        page: { type: "integer", optional: true, default: 1 },
        page_size: { type: "integer", optional: true, default: 50 },
        sort: {
          type: "string",
          optional: true,
          default: "stock_value_desc",
          enum: ["stock_value_desc", "quantity_desc"],
        },
      },
    });
    expect(params.only_positive).toBeUndefined();
    expect(params.page).toBeUndefined();
    expect(params.page_size).toBeUndefined();
    expect(params.sort).toBeUndefined();
  });
});
