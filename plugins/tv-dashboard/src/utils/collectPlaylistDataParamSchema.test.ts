import { describe, expect, it } from "vitest";
import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  asDataFilterValues,
  collectDataOperationIds,
  collectFetchableOperationIds,
  collectPlaylistDataParamSchema,
  collectPlaylistOperationIds,
  collectSlideDataParamSchema,
  mergeRouteParamSchemas,
  mergeRouteParamSchemasDetailed,
  omitSchemaKeysCoveredByDefaults,
} from "./collectPlaylistDataParamSchema";
import type { ComunicadoBlock, TvDataModel } from "@delpi/tv-dashboard-presentation";

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
      "excludeWeekends",
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
    expect(Object.keys(schema).sort()).toEqual([
      "branch",
      "excludeWeekends",
      "granularity",
      "top_limit",
    ]);
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

  it("MODEL_ONLY_PLAYLIST_FILTERS_VISIBLE: slide só-DataModel contribui operationIds dos inputs", () => {
    const slides = [
      {
        nativeConfig: {
          version: 4,
          blocks: [
            { id: "v1", type: "kpi_view", modelId: "m1" },
          ],
          dataModels: [
            {
              id: "m1",
              label: "Modelo",
              primaryInputId: "in1",
              inputs: [
                { id: "in1", operationId: "get_oee", params: {} },
                { id: "in2", operationId: "get_stock", params: {} },
              ],
            },
          ],
        },
      },
    ];
    expect(collectPlaylistOperationIds(slides).sort()).toEqual(["get_oee", "get_stock"]);
    const schema = collectPlaylistDataParamSchema(slides, routes);
    expect(schema.branch).toBeTruthy();
    expect(schema.top_limit).toBeTruthy();
    expect(schema.page).toBeUndefined();
  });

  it("MODEL_ONLY_SLIDE_FILTERS_VISIBLE: collectSlideDataParamSchema usa inputs do modelo", () => {
    const nativeConfig = {
      version: 4,
      blocks: [{ id: "v1", type: "chart_view", modelId: "m1" }],
      dataModels: [
        {
          id: "m1",
          label: "Modelo",
          primaryInputId: "in1",
          inputs: [{ id: "in1", operationId: "get_stock", params: {} }],
        },
      ],
    };
    const schema = collectSlideDataParamSchema(nativeConfig, routes);
    expect(Object.keys(schema).sort()).toEqual([
      "branch",
      "excludeWeekends",
      "granularity",
      "top_limit",
    ]);
  });

  it("MIXED_LEGACY_MODEL_FILTER_UNION: fonte legacy + DataModel unem sem duplicar", () => {
    const nativeConfig = {
      version: 4,
      blocks: [
        {
          id: "s1",
          type: "data_source",
          dataBinding: { operationId: "get_oee", params: {} },
        },
        { id: "v1", type: "table_view", modelId: "m1" },
      ],
      dataModels: [
        {
          id: "m1",
          label: "Modelo",
          primaryInputId: "in1",
          inputs: [{ id: "in1", operationId: "get_stock", params: {} }],
        },
      ],
    };
    const schema = collectSlideDataParamSchema(nativeConfig, routes);
    expect(Object.keys(schema).sort()).toEqual([
      "branch",
      "end_date",
      "excludeWeekends",
      "granularity",
      "start_date",
      "top_limit",
    ]);
  });

  it("collectDataOperationIds cobre blocos fetchable + inputs de modelo (dedup)", () => {
    const ids = collectDataOperationIds({
      blocks: [
        {
          id: "s1",
          type: "data_source",
          dataBinding: { operationId: "get_oee", params: {} },
        },
      ] as ComunicadoBlock[],
      dataModels: [
        {
          id: "m1",
          inputs: [
            { id: "a", operationId: "get_oee" },
            { id: "b", operationId: "get_stock" },
            { id: "c", operationId: "  " },
          ],
        } as TvDataModel,
      ],
    });
    expect(ids.sort()).toEqual(["get_oee", "get_stock"]);
  });

  it("MODEL_FILTER_SCHEMA_CONFLICT_SAFE: tipo divergente sai do agregado e vira conflito", () => {
    const conflictRoutes: TvDataRouteCatalogItem[] = [
      {
        operationId: "route_a",
        category: "x",
        path: "/a",
        label: "A",
        paramSchema: { period: { type: "string", format: "date" } },
      },
      {
        operationId: "route_b",
        category: "x",
        path: "/b",
        label: "B",
        paramSchema: { period: { type: "integer" } },
      },
    ];
    const { schema, conflicts } = mergeRouteParamSchemasDetailed(conflictRoutes, [
      "route_a",
      "route_b",
    ]);
    expect(schema.period).toBeUndefined();
    expect(conflicts).toEqual([
      { key: "period", operationIds: ["route_a", "route_b"] },
    ]);
  });

  it("MODEL_FILTER_SCHEMA_CONFLICT_SAFE: enums disjuntos conflitam; interseção mergeia", () => {
    const enumRoutes: TvDataRouteCatalogItem[] = [
      {
        operationId: "route_a",
        category: "x",
        path: "/a",
        label: "A",
        paramSchema: {
          branch: { type: "string", enum: ["01", "02"] },
          shared: { type: "string", enum: ["x", "y"] },
        },
      },
      {
        operationId: "route_b",
        category: "x",
        path: "/b",
        label: "B",
        paramSchema: {
          branch: { type: "string", enum: ["SC", "ES"] },
          shared: { type: "string", enum: ["y", "z"] },
        },
      },
    ];
    const { schema, conflicts } = mergeRouteParamSchemasDetailed(enumRoutes, [
      "route_a",
      "route_b",
    ]);
    expect(schema.branch).toBeUndefined();
    expect(conflicts.map((c) => c.key)).toEqual(["branch"]);
    expect(schema.shared?.enum).toEqual(["y"]);
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
