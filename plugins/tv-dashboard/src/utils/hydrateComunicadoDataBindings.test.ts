import { describe, expect, it } from "vitest";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  buildLabelCatalogFromRoutes,
  hydrateComunicadoDataBindings,
} from "./hydrateComunicadoDataBindings";

const ppmRoute: TvDataRouteCatalogItem = {
  operationId: "get_ppm_internal_summary",
  label: "PPM Interno — realizado",
  labelAliases: ["Qualidade — PPM interno"],
  category: "quality",
  paramSchema: {
    start_date: { type: "string" },
    end_date: { type: "string" },
    branch: { type: "string", optional: true },
  },
};

function sourceBlock(
  operationId: string,
  opts: { label?: string; params?: Record<string, string | number | boolean> } = {},
) {
  return {
    id: `src-${operationId}`,
    type: "data_source" as const,
    frame: { x: 0, y: 0, w: 10, h: 10 },
    dataBinding: {
      operationId,
      params: opts.params ?? {},
      displayMode: "auto" as const,
      label: opts.label,
    },
  };
}

describe("hydrateComunicadoDataBindings", () => {
  it("limpa label catalog-like e remapeia date_start", () => {
    const config = {
      version: 4 as const,
      blocks: [
        sourceBlock("get_ppm_internal_summary", {
          label: "Qualidade — PPM interno",
          params: { date_start: "2026-01-01", date_end: "2026-01-31", obsolete: "x" },
        }),
      ],
    };
    const result = hydrateComunicadoDataBindings(config, [ppmRoute]);
    expect(result.changed).toBe(true);
    expect(result.clearedLabels).toBe(1);
    const binding =
      result.config.blocks?.[0] && "dataBinding" in result.config.blocks[0]
        ? result.config.blocks[0].dataBinding
        : null;
    expect(binding?.label).toBeUndefined();
    expect(binding?.params?.start_date).toBe("2026-01-01");
    expect(binding?.params?.end_date).toBe("2026-01-31");
    expect(binding?.params).not.toHaveProperty("date_start");
    expect(binding?.params).not.toHaveProperty("obsolete");
    expect(result.strippedParamKeys).toContain("obsolete");
  });

  it("preserva rótulo customizado", () => {
    const result = hydrateComunicadoDataBindings(
      {
        version: 4,
        blocks: [sourceBlock("get_ppm_internal_summary", { label: "Meu KPI" })],
      },
      [ppmRoute],
    );
    const binding =
      result.config.blocks?.[0] && "dataBinding" in result.config.blocks[0]
        ? result.config.blocks[0].dataBinding
        : null;
    expect(binding?.label).toBe("Meu KPI");
  });

  it("marca rota órfã sem apagar o bloco", () => {
    const result = hydrateComunicadoDataBindings(
      { version: 4, blocks: [sourceBlock("get_gone_route", { params: { a: 1 } })] },
      [ppmRoute],
    );
    expect(result.orphanOperationIds).toEqual(["get_gone_route"]);
    expect(result.config.blocks).toHaveLength(1);
  });
});

describe("buildLabelCatalogFromRoutes", () => {
  it("expõe label vivo por operationId (mesmo input da aba Dados no Elemento)", () => {
    const catalog = buildLabelCatalogFromRoutes([ppmRoute]);
    expect(catalog.get_ppm_internal_summary).toEqual({
      label: "PPM Interno — realizado",
      labelAliases: ["Qualidade — PPM interno"],
    });
  });
});
