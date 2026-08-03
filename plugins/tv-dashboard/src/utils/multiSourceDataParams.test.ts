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

  it("valores iguais aparecem; divergentes ficam vazios", () => {
    const schema = buildMultiSourceParamSchema(routes, [
      source("a", "get_refugo", { branch: "01", periodDays: 30 }),
      source("b", "get_retrabalho", { branch: "01", periodDays: 7 }),
    ]);
    expect(
      resolveSharedParamDisplayValues(
        [
          source("a", "get_refugo", { branch: "01", periodDays: 30 }),
          source("b", "get_retrabalho", { branch: "01", periodDays: 7 }),
        ],
        schema,
      ),
    ).toEqual({
      branch: "01",
      periodDays: "",
      granularity: "",
    });
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
});

// type guard smoke for ComunicadoBlock casting in tests
void (null as unknown as ComunicadoBlock);
