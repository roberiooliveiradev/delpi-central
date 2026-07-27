import { describe, expect, it } from "vitest";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  resolveOperationIdForDataBoundBlock,
  resolveRouteForDataBoundBlock,
} from "./resolveDataBoundBlockRoute";

const routes: TvDataRouteCatalogItem[] = [
  {
    operationId: "get_transformometro_savings_investment_series",
    label: "Economia bruta vs Investimento do TRANSFORMA+",
    category: "engineering",
    paramSchema: {},
  },
];

describe("resolveDataBoundBlockRoute", () => {
  it("resolve operationId direto da fonte", () => {
    const source = {
      id: "src1",
      type: "data_source" as const,
      frame: { x: 0, y: 0, w: 1, h: 1 },
      dataBinding: {
        operationId: "get_transformometro_savings_investment_series",
        params: {},
        displayMode: "auto" as const,
      },
    };
    expect(resolveOperationIdForDataBoundBlock(source, [source])).toBe(
      "get_transformometro_savings_investment_series",
    );
  });

  it("resolve rota via dataSourceId do chart_view (Elemento ≡ Dados)", () => {
    const source = {
      id: "src1",
      type: "data_source" as const,
      frame: { x: 0, y: 0, w: 1, h: 1 },
      dataBinding: {
        operationId: "get_transformometro_savings_investment_series",
        params: {},
        displayMode: "auto" as const,
      },
    };
    const chart = {
      id: "c1",
      type: "chart_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartType: "line" as const,
      dataSourceId: "src1",
    };
    const blocks = [source, chart];
    expect(resolveOperationIdForDataBoundBlock(chart, blocks)).toBe(
      "get_transformometro_savings_investment_series",
    );
    expect(resolveRouteForDataBoundBlock(chart, blocks, routes)?.label).toBe(
      "Economia bruta vs Investimento do TRANSFORMA+",
    );
  });

  it("resolve kpi_view e table_view da mesma forma", () => {
    const source = {
      id: "src1",
      type: "data_source" as const,
      frame: { x: 0, y: 0, w: 1, h: 1 },
      dataBinding: {
        operationId: "get_transformometro_savings_investment_series",
        params: {},
        displayMode: "auto" as const,
      },
    };
    for (const type of ["kpi_view", "table_view"] as const) {
      const view = {
        id: `v-${type}`,
        type,
        frame: { x: 0, y: 0, w: 20, h: 20 },
        dataSourceId: "src1",
        ...(type === "table_view" ? { tablePreset: "plain" as const } : {}),
      };
      expect(resolveRouteForDataBoundBlock(view as never, [source, view as never], routes)?.label).toContain(
        "Economia bruta",
      );
    }
  });
});
