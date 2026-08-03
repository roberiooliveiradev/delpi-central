import { describe, expect, it } from "vitest";

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  buildMultiSourceParamPatches,
  buildMultiSourceParamSchema,
  resolveSharedParamDisplayValues,
  type MultiSourceBindingTarget,
} from "./multiSourceDataParams";

function source(
  id: string,
  operationId: string,
  params: Record<string, string | number | boolean> = {},
): MultiSourceBindingTarget {
  return {
    id,
    type: "data_source",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    dataBinding: { operationId, params, displayMode: "auto" },
  };
}

const routes: TvDataRouteCatalogItem[] = [
  {
    operationId: "get_refugo",
    label: "Refugo",
    category: "quality",
    paramSchema: {
      branch: { type: "string", label: "Filial" },
      periodDays: { type: "integer", label: "Dias" },
      page: { type: "integer", label: "Página" },
    },
  },
  {
    operationId: "get_retrabalho",
    label: "Retrabalho",
    category: "quality",
    paramSchema: {
      branch: { type: "string", label: "Filial" },
      periodDays: { type: "integer", label: "Dias" },
      granularity: { type: "string", label: "Granularidade" },
    },
  },
];

describe("multiSourceDataParams", () => {
  it("une schemas sem repetir chave e sem paginação", () => {
    const schema = buildMultiSourceParamSchema(routes, [
      source("a", "get_refugo"),
      source("b", "get_retrabalho"),
    ]);
    expect(Object.keys(schema).sort()).toEqual(["branch", "granularity", "periodDays"]);
    expect(schema.page).toBeUndefined();
  });

  it("valores iguais aparecem; divergentes ficam vazios e em divergedKeys", () => {
    const schema = buildMultiSourceParamSchema(routes, [
      source("a", "get_refugo", { branch: "01", periodDays: 30 }),
      source("b", "get_retrabalho", { branch: "01", periodDays: 7 }),
    ]);
    const shared = resolveSharedParamDisplayValues(
      [
        source("a", "get_refugo", { branch: "01", periodDays: 30 }),
        source("b", "get_retrabalho", { branch: "01", periodDays: 7 }),
      ],
      schema,
    );
    expect(shared.values).toEqual({
      branch: "01",
      periodDays: "",
      granularity: "",
    });
    expect([...shared.divergedKeys].sort()).toEqual(["periodDays"]);
  });

  it("aplica update só nas fontes que têm a chave no schema", () => {
    const targets = [
      source("a", "get_refugo", { branch: "01" }),
      source("b", "get_retrabalho", { branch: "01" }),
    ];
    const patches = buildMultiSourceParamPatches(targets, routes, {
      periodDays: "15",
      granularity: "month",
    });
    expect(patches).toHaveLength(2);
    const byId = Object.fromEntries(patches.map((item) => [item.blockId, item.patch]));
    const aParams = (byId.a?.dataBinding as { params?: Record<string, unknown> } | undefined)
      ?.params;
    const bParams = (byId.b?.dataBinding as { params?: Record<string, unknown> } | undefined)
      ?.params;
    expect(aParams).toMatchObject({ branch: "01", periodDays: 15 });
    expect(aParams).not.toHaveProperty("granularity");
    expect(bParams).toMatchObject({ branch: "01", periodDays: 15, granularity: "month" });
  });

  it("não gera patch quando a fonte não aceita nenhuma chave do update", () => {
    const targets = [source("a", "get_refugo", { branch: "01" })];
    expect(
      buildMultiSourceParamPatches(targets, routes, { granularity: "month" }),
    ).toEqual([]);
  });

  it("aplica dateRangePreset em fontes com par de datas mesmo fora do OpenAPI", () => {
    const datedRoutes: TvDataRouteCatalogItem[] = [
      {
        operationId: "get_ppm_a",
        label: "PPM A",
        category: "quality",
        paramSchema: {
          branch: { type: "string" },
          start_date: { type: "string", format: "date" },
          end_date: { type: "string", format: "date" },
        },
      },
      {
        operationId: "get_ppm_b",
        label: "PPM B",
        category: "quality",
        paramSchema: {
          branch: { type: "string" },
          date_start: { type: "string", format: "date" },
          date_end: { type: "string", format: "date" },
        },
      },
      {
        operationId: "get_static",
        label: "Sem datas",
        category: "quality",
        paramSchema: {
          branch: { type: "string" },
        },
      },
    ];
    const targets = [
      source("a", "get_ppm_a", { branch: "01", start_date: "2026-01-01", end_date: "2026-01-31" }),
      source("b", "get_ppm_b", {
        branch: "01",
        date_start: "2026-01-01",
        date_end: "2026-01-31",
      }),
      source("c", "get_static", { branch: "01" }),
    ];
    const patches = buildMultiSourceParamPatches(targets, datedRoutes, {
      dateRangePreset: "this_month",
      start_date: "",
      end_date: "",
      competence: "",
    });
    expect(patches.map((item) => item.blockId).sort()).toEqual(["a", "b"]);
    const byId = Object.fromEntries(patches.map((item) => [item.blockId, item.patch]));
    const aParams = (byId.a?.dataBinding as { params?: Record<string, unknown> }).params;
    const bParams = (byId.b?.dataBinding as { params?: Record<string, unknown> }).params;
    expect(aParams).toMatchObject({ branch: "01", dateRangePreset: "this_month" });
    expect(aParams).not.toHaveProperty("start_date");
    expect(aParams).not.toHaveProperty("end_date");
    expect(bParams).toMatchObject({ branch: "01", dateRangePreset: "this_month" });
    expect(bParams).not.toHaveProperty("date_start");
    expect(bParams).not.toHaveProperty("date_end");
  });

  it("exibe dateRangePreset compartilhado na multi-seleção", () => {
    const datedRoutes: TvDataRouteCatalogItem[] = [
      {
        operationId: "get_ppm_a",
        label: "PPM A",
        category: "quality",
        paramSchema: {
          start_date: { type: "string" },
          end_date: { type: "string" },
        },
      },
      {
        operationId: "get_ppm_b",
        label: "PPM B",
        category: "quality",
        paramSchema: {
          start_date: { type: "string" },
          end_date: { type: "string" },
        },
      },
    ];
    const schema = buildMultiSourceParamSchema(datedRoutes, [
      source("a", "get_ppm_a", { dateRangePreset: "this_month" }),
      source("b", "get_ppm_b", { dateRangePreset: "this_month" }),
    ]);
    expect(
      resolveSharedParamDisplayValues(
        [
          source("a", "get_ppm_a", { dateRangePreset: "this_month" }),
          source("b", "get_ppm_b", { dateRangePreset: "this_month" }),
        ],
        schema,
      ).values.dateRangePreset,
    ).toBe("this_month");
  });
});

// type guard smoke for ComunicadoBlock casting in tests
void (null as unknown as ComunicadoBlock);
