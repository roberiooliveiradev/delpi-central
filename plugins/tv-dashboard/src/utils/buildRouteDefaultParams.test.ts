import { describe, expect, it } from "vitest";

import { buildRouteDefaultParams, CONVENIENT_REQUIRED_DEFAULTS } from "./buildRouteDefaultParams";

describe("buildRouteDefaultParams", () => {
  it("aplica defaultParams, schema.default, filial e preset de datas", () => {
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
    expect(params.periodDays).toBe(30);
    expect(params.granularity).toBe("day");
    expect(params.dateRangePreset).toBe("this_month");
  });

  it("usa filial SC em rotas de agendamento", () => {
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
    expect(params.dateRangePreset).toBe("this_month");
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
});
