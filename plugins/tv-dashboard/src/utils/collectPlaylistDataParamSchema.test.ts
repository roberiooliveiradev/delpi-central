import { describe, expect, it } from "vitest";
import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  asDataFilterValues,
  collectFetchableOperationIds,
  collectPlaylistDataParamSchema,
  collectPlaylistOperationIds,
  collectSlideDataParamSchema,
  mergeRouteParamSchemas,
  omitSchemaKeysCoveredByDefaults,
} from "./collectPlaylistDataParamSchema";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

const routes: TvDataRouteCatalogItem[] = [
  {
    operationId: "get_oee",
    category: "production",
    path: "/oee",
    label: "OEE",
    paramSchema: {
      branch: { type: "string", label: "Filial" },
      start_date: { type: "string", format: "date" },
      end_date: { type: "string", format: "date" },
      page: { type: "integer", label: "Página" },
      page_size: { type: "integer", label: "Tamanho" },
      granularity: { type: "string", label: "Granularidade" },
    },
    fixedQueryParams: { granularity: "day" },
  },
  {
    operationId: "get_stock",
    category: "supplies",
    path: "/stock",
    label: "Estoque",
    paramSchema: {
      branch: { type: "string", label: "Filial estoque" },
      top_limit: { type: "integer", label: "Top" },
      granularity: { type: "string", label: "Granularidade" },
    },
  },
  {
    operationId: "get_unused",
    category: "other",
    path: "/x",
    label: "Unused",
    paramSchema: {
      weird: { type: "string", label: "Não deve aparecer" },
    },
  },
];

describe("collectPlaylistDataParamSchema", () => {
  it("coleta operationIds só de blocos fetchable", () => {
    const blocks = [
      {
        id: "1",
        type: "data_source",
        dataBinding: { operationId: "get_oee", params: {} },
      },
      {
        id: "2",
        type: "text",
        content: "oi",
      },
      {
        id: "3",
        type: "data_kpi",
        dataBinding: { operationId: "get_stock", params: {} },
      },
    ] as ComunicadoBlock[];
    expect(collectFetchableOperationIds(blocks).sort()).toEqual(["get_oee", "get_stock"]);
  });

  it("une schemas sem repetir chave, sem paginação e sem rotas não usadas", () => {
    const slides = [
      {
        nativeConfig: {
          version: 4,
          blocks: [
            {
              id: "s1",
              type: "data_source",
              dataBinding: { operationId: "get_oee", params: {} },
            },
          ],
        },
      },
      {
        nativeConfig: {
          version: 4,
          blocks: [
            {
              id: "s2",
              type: "data_source",
              dataBinding: { operationId: "get_stock", params: {} },
            },
            {
              id: "s3",
              type: "data_source",
              dataBinding: { operationId: "get_oee", params: {} },
            },
          ],
        },
      },
    ];
    expect(collectPlaylistOperationIds(slides).sort()).toEqual(["get_oee", "get_stock"]);
    const schema = collectPlaylistDataParamSchema(slides, routes);
    expect(Object.keys(schema).sort()).toEqual([
      "branch",
      "end_date",
      "granularity",
      "start_date",
      "top_limit",
    ]);
    expect(schema.branch?.label).toBe("Filial");
    expect(schema.page).toBeUndefined();
    expect(schema.page_size).toBeUndefined();
    expect(schema.weird).toBeUndefined();
  });

  it("respeita fixedQueryParams ao unir (não expõe param fixo da rota)", () => {
    const schema = mergeRouteParamSchemas(routes, ["get_oee"]);
    expect(schema.granularity).toBeUndefined();
    expect(schema.branch).toBeTruthy();
  });

  it("schema do slide ignora outras telas e mantém chaves também presentes na programação", () => {
    const nativeConfig = {
      version: 4,
      blocks: [
        {
          id: "s1",
          type: "data_source",
          dataBinding: { operationId: "get_stock", params: {} },
        },
      ],
    };
    const schema = collectSlideDataParamSchema(nativeConfig, routes);
    expect(Object.keys(schema).sort()).toEqual(["branch", "granularity", "top_limit"]);
    expect(schema.branch).toBeTruthy();
  });

  it("omitSchemaKeysCoveredByDefaults cobre período e par de datas (helper legado)", () => {
    const schema = {
      dateRangePreset: { type: "string" },
      periodDays: { type: "integer" },
      start_date: { type: "string" },
      end_date: { type: "string" },
      branch: { type: "string" },
    };
    const next = omitSchemaKeysCoveredByDefaults(schema, { dateRangePreset: "this_month" });
    expect(Object.keys(next)).toEqual(["branch"]);
  });

  it("mergeRouteParamSchemas deduplica por chave", () => {
    const schema = mergeRouteParamSchemas(routes, ["get_oee", "get_stock"]);
    expect(schema.branch?.label).toBe("Filial");
  });

  it("asDataFilterValues normaliza tipos", () => {
    expect(asDataFilterValues({ branch: "01", periodDays: 7, flag: true, x: null })).toEqual({
      branch: "01",
      periodDays: 7,
      flag: true,
      x: null,
    });
  });
});
