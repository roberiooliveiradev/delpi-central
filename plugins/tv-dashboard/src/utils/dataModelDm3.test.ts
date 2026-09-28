import { describe, expect, it } from "vitest";

import type {
  ComunicadoBlock,
  ComunicadoKpiViewBlock,
  ComunicadoTableViewBlock,
  TvDataModel,
} from "@delpi/tv-dashboard-presentation";

import { linkedChartSeriesForSource } from "./dataPrepareCrossHighlight";
import { serializeDataModelForPreview, stripBlockResolvedForPreview } from "./dataPreviewRequest";
import { renameKpiMetricFieldLabel } from "./renameKpiMetricFieldLabel";
import { renameTableColumnFieldLabel } from "./renameTableColumnFieldLabel";
import { resolveOperationIdForDataBoundBlock } from "./resolveDataBoundBlockRoute";
import { resolveSelectedDataContext } from "./selectedDataContext";

function makeModel(overrides: Partial<TvDataModel> = {}): TvDataModel {
  return {
    id: "m1",
    label: "ROL consolidado",
    primaryInputId: "in-a",
    inputs: [
      {
        id: "in-a",
        operationId: "commercial.rol.summary",
        label: "Atual",
        params: { dateRangePreset: "current_year" },
      },
      { id: "in-b", operationId: "commercial.rol.summary", label: "Anterior" },
    ],
    fieldLabels: { rol: "ROL" },
    ...overrides,
  };
}

function makeView(overrides: Record<string, unknown> = {}): ComunicadoBlock {
  return {
    id: "view-1",
    type: "kpi_view",
    frame: { x: 0, y: 0, w: 20, h: 10 },
    style: { zIndex: 1 },
    ...overrides,
  } as ComunicadoBlock;
}

function makeSource(id = "src-1"): ComunicadoBlock {
  return {
    id,
    type: "data_source",
    frame: { x: 0, y: 0, w: 10, h: 5 },
    style: { zIndex: 0 },
    dataBinding: { operationId: "commercial.rol.summary" },
  } as ComunicadoBlock;
}

describe("serializeDataModelForPreview — whitelist persistido", () => {
  it("envia só campos persistidos; artefatos de runtime fora", () => {
    const dirty = {
      ...makeModel(),
      resolved: { kpiMetrics: [] },
      outputSchema: { fields: ["rol"] },
      runtimeErrors: ["boom"],
      inputs: [
        {
          id: "in-a",
          operationId: "commercial.rol.summary",
          label: "Atual",
          params: { dateRangePreset: "current_year" },
          resolved: { rows: [] },
          effectiveParams: { x: 1 },
        },
      ],
    } as unknown as TvDataModel;
    const payload = serializeDataModelForPreview(dirty);
    expect(payload).toEqual({
      id: "m1",
      primaryInputId: "in-a",
      inputs: [
        {
          id: "in-a",
          operationId: "commercial.rol.summary",
          label: "Atual",
          params: { dateRangePreset: "current_year" },
        },
      ],
      label: "ROL consolidado",
      fieldLabels: { rol: "ROL" },
    });
    expect(payload).not.toHaveProperty("resolved");
    expect(payload).not.toHaveProperty("outputSchema");
    expect(payload).not.toHaveProperty("runtimeErrors");
    const input = (payload.inputs as Record<string, unknown>[])[0]!;
    expect(input).not.toHaveProperty("resolved");
    expect(input).not.toHaveProperty("effectiveParams");
  });

  it("preserva transforms de input e do modelo", () => {
    const model = makeModel({
      transform: { v: 1, steps: [{ op: "select", columns: ["rol"] }] },
      inputs: [
        {
          id: "in-a",
          operationId: "op",
          transform: { v: 2, steps: [] },
        },
      ],
    });
    const payload = serializeDataModelForPreview(model);
    expect(payload.transform).toEqual({ v: 1, steps: [{ op: "select", columns: ["rol"] }] });
    expect((payload.inputs as Record<string, unknown>[])[0]?.transform).toEqual({
      v: 2,
      steps: [],
    });
  });
});

describe("stripBlockResolvedForPreview", () => {
  it("remove resolved do body sem mutar o original", () => {
    const block = { id: "b1", type: "data_source", resolved: { rows: [] } };
    const clean = stripBlockResolvedForPreview(block);
    expect(clean).not.toHaveProperty("resolved");
    expect(block.resolved).toBeDefined();
  });
});

describe("resolveSelectedDataContext — model-aware", () => {
  const models = [makeModel()];

  it("visual com modelId → bindingModel resolvido, bindingTarget null", () => {
    const view = makeView({ modelId: "m1" });
    const ctx = resolveSelectedDataContext([view], ["view-1"], models);
    expect(ctx.kind).toBe("single");
    expect(ctx.bindingModel?.id).toBe("m1");
    // Modelo não é bloco — o target legacy resolve null (sem fonte ligada).
    expect(ctx.bindingTarget).toBeNull();
  });

  it("modelId vence: visual com ambos ids resolve o modelo", () => {
    const source = makeSource("src-1");
    const view = makeView({ modelId: "m1", dataSourceId: "src-1" });
    const ctx = resolveSelectedDataContext([source, view], ["view-1"], models);
    expect(ctx.bindingModel?.id).toBe("m1");
    expect(ctx.bindingTarget).toBeNull();
  });

  it("visual legacy dataSourceId → bindingTarget = fonte, sem modelo", () => {
    const source = makeSource("src-1");
    const view = makeView({ dataSourceId: "src-1" });
    const ctx = resolveSelectedDataContext([source, view], ["view-1"], models);
    expect(ctx.bindingModel).toBeNull();
    expect(ctx.bindingTarget?.id).toBe("src-1");
  });

  it("mixed: visual de modelo + visual de fonte no mesmo slide", () => {
    const source = makeSource("src-1");
    const modelView = makeView({ id: "view-m", modelId: "m1" });
    const sourceView = makeView({ id: "view-s", dataSourceId: "src-1" });
    const ctx = resolveSelectedDataContext(
      [source, modelView, sourceView],
      ["view-m", "view-s"],
      models,
    );
    expect(ctx.kind).toBe("mixed");
    // Último selecionado (view-s) define o primary — source-bound.
    expect(ctx.primary?.id).toBe("view-s");
    expect(ctx.bindingTargets.map((t) => t.id)).toContain("src-1");
  });
});

describe("renameKpiMetricFieldLabel — model target", () => {
  it("modelId: fieldLabels do modelo + projeção limpa, sem sourcePatch", () => {
    const kpi = {
      ...makeView({ modelId: "m1" }),
      kpiProjection: {
        metrics: [{ field: "rol", label: "ROL" }],
      },
    } as ComunicadoBlock;
    const result = renameKpiMetricFieldLabel({
      blocks: [kpi],
      kpiBlock: kpi as ComunicadoKpiViewBlock,
      field: "rol",
      label: "Receita",
      dataModels: [makeModel()],
    });
    expect(result.sourcePatch).toBeUndefined();
    expect(result.modelPatch?.id).toBe("m1");
    expect(result.modelPatch?.fieldLabels).toEqual({ rol: "Receita" });
    // label local limpo → label canônico do modelo cascateia
    expect(result.kpiProjection?.metrics?.[0]?.label).toBeUndefined();
  });

  it("dataSourceId legacy: mantém patch na fonte (sem modelPatch)", () => {
    const source = {
      ...makeSource("src-1"),
      fieldLabels: { rol: "ROL" },
    } as ComunicadoBlock;
    const kpi = {
      ...makeView({ dataSourceId: "src-1" }),
      kpiProjection: {
        metrics: [{ field: "rol", label: "ROL" }],
      },
    } as ComunicadoBlock;
    const result = renameKpiMetricFieldLabel({
      blocks: [source, kpi],
      kpiBlock: kpi as ComunicadoKpiViewBlock,
      field: "rol",
      label: "Receita",
      dataModels: [makeModel()],
    });
    expect(result.modelPatch).toBeUndefined();
    expect(result.sourcePatch?.id).toBe("src-1");
    expect(result.sourcePatch?.fieldLabels).toEqual({ rol: "Receita" });
  });
});

describe("renameTableColumnFieldLabel — model target", () => {
  it("modelId: escreve fieldLabels do modelo, não da fonte", () => {
    const table = {
      ...makeView({ id: "tbl-1", type: "table_view", modelId: "m1" }),
      tableProjection: {
        columns: [{ key: "rol", label: "ROL", field: "rol" }],
      },
    } as unknown as ComunicadoBlock;
    const result = renameTableColumnFieldLabel({
      blocks: [table],
      tableBlock: table as ComunicadoTableViewBlock,
      columnKey: "rol",
      label: "Receita",
      dataModels: [makeModel()],
    });
    expect(result.sourcePatch).toBeUndefined();
    expect(result.modelPatch?.fieldLabels).toEqual({ rol: "Receita" });
    expect(result.tableProjection?.columns?.[0]?.label).toBeUndefined();
  });
});

describe("resolveOperationIdForDataBoundBlock — model target", () => {
  it("visual model-bound resolve operationId do primaryInput do modelo", () => {
    const view = makeView({ modelId: "m1" });
    expect(
      resolveOperationIdForDataBoundBlock(view, [view], [makeModel()]),
    ).toBe("commercial.rol.summary");
  });

  it("model sem primaryInput cai no primeiro input", () => {
    const model = makeModel({ primaryInputId: "" });
    const view = makeView({ modelId: "m1" });
    expect(
      resolveOperationIdForDataBoundBlock(view, [view], [model]),
    ).toBe("commercial.rol.summary");
  });

  it("negativo: modelId inexistente → null; fonte continua resolvendo", () => {
    const view = makeView({ modelId: "missing" });
    expect(
      resolveOperationIdForDataBoundBlock(view, [view], [makeModel()]),
    ).toBeNull();
    const source = makeSource("src-1");
    const legacy = makeView({ dataSourceId: "src-1" });
    expect(
      resolveOperationIdForDataBoundBlock(legacy, [source, legacy], [makeModel()]),
    ).toBe("commercial.rol.summary");
  });
});

describe("linkedChartSeriesForSource — target-aware", () => {
  it("chart com modelId não casa com highlight da fonte", () => {
    const chartBlock = {
      ...makeView({ id: "chart-1", type: "chart_view", modelId: "m1" }),
      chartProjection: {
        series: [{ field: "rol", label: "ROL" }],
      },
    } as ComunicadoBlock;
    expect(linkedChartSeriesForSource([chartBlock], "src-1")).toHaveLength(0);
  });

  it("chart source-bound casa séries da fonte", () => {
    const chartBlock = {
      ...makeView({ id: "chart-1", type: "chart_view", dataSourceId: "src-1" }),
      chartProjection: {
        series: [{ field: "rol", label: "ROL" }],
      },
    } as ComunicadoBlock;
    const series = linkedChartSeriesForSource([chartBlock], "src-1");
    expect(series).toHaveLength(1);
    expect(series[0]?.chartId).toBe("chart-1");
    expect(series[0]?.field).toBe("rol");
  });

  it("chart model-bound casa séries pelo id do modelo", () => {
    const chartBlock = {
      ...makeView({ id: "chart-1", type: "chart_view", modelId: "m1" }),
      chartProjection: {
        series: [{ field: "rol", label: "ROL" }],
      },
    } as ComunicadoBlock;
    const series = linkedChartSeriesForSource([chartBlock], "m1");
    expect(series).toHaveLength(1);
  });
});
