import { describe, expect, it } from "vitest";

import {
  applyCanvasTableCellDataSourceId,
  applyCanvasTableCellModelId,
  bindingTargetId,
  bindingTargetKind,
  buildCanvasTableDataLinkPatch,
  buildTextDataLinkPatch,
  buildViewDataLinkPatch,
  canvasTableHasDataBinding,
  collectCanvasTableSourceIds,
  dataModelOptionsForInspector,
  findDataModel,
  getLinkedDataSourceIds,
  isRenderableBlockType,
  isTechnicalDataBlockType,
  listViewsLinkedToDataSource,
  normalizeCanvasTableCells,
  normalizeDataModels,
  planDataModelPreviewRefresh,
  buildDataPreviewFingerprint,
  resolveCanvasTableCellSourceId,
  shouldHideDataSourceOnStage,
  textBlockHasDataBinding,
  textBlockHasLinkedDataSource,
  type ComunicadoBlock,
  type ComunicadoCanvasTableBlock,
  type ComunicadoConfig,
  type TvDataModel,
} from "./index";

function makeModel(overrides: Partial<TvDataModel> = {}): TvDataModel {
  return {
    id: "m1",
    label: "ROL consolidado",
    primaryInputId: "in-a",
    inputs: [
      { id: "in-a", operationId: "commercial.rol.summary", label: "Atual" },
      { id: "in-b", operationId: "commercial.rol.summary", label: "Anterior" },
    ],
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

function makeCanvasTable(overrides: Record<string, unknown> = {}): ComunicadoCanvasTableBlock {
  return {
    id: "grade-1",
    type: "canvas_table",
    rows: 2,
    cols: 2,
    cells: normalizeCanvasTableCells([], 2, 2),
    frame: { x: 0, y: 0, w: 40, h: 20 },
    style: { zIndex: 1 },
    ...overrides,
  } as ComunicadoCanvasTableBlock;
}

describe("bindingTargetId / bindingTargetKind (contrato DM2)", () => {
  it("modelId vence sobre dataSourceId quando ambos presentes", () => {
    const block = makeView({ modelId: "m1", dataSourceId: "src-1" });
    expect(bindingTargetId(block)).toBe("m1");
    expect(bindingTargetKind(block)).toBe("model");
  });

  it("dataSourceId puro resolve source", () => {
    const block = makeView({ dataSourceId: "src-1" });
    expect(bindingTargetId(block)).toBe("src-1");
    expect(bindingTargetKind(block)).toBe("source");
  });

  it("modelId puro resolve model", () => {
    const block = makeView({ modelId: " m1 " });
    expect(bindingTargetId(block)).toBe("m1");
    expect(bindingTargetKind(block)).toBe("model");
  });

  it("sem binding retorna vazio/null", () => {
    const block = makeView();
    expect(bindingTargetId(block)).toBe("");
    expect(bindingTargetKind(block)).toBeNull();
    expect(bindingTargetId(null)).toBe("");
    expect(bindingTargetKind(undefined)).toBeNull();
  });
});

describe("findDataModel / dataModelOptionsForInspector", () => {
  const config: ComunicadoConfig = { dataModels: [makeModel()] };

  it("localiza modelo por id e ignora vazio", () => {
    expect(findDataModel(config, "m1")?.id).toBe("m1");
    expect(findDataModel(config, "inexistente")).toBeNull();
    expect(findDataModel(config, "")).toBeNull();
    expect(findDataModel(null, "m1")).toBeNull();
  });

  it("opções usam label com fallback para id", () => {
    const options = dataModelOptionsForInspector({
      dataModels: [makeModel(), makeModel({ id: "m2", label: undefined })],
    });
    expect(options).toEqual([
      { value: "m1", label: "ROL consolidado" },
      { value: "m2", label: "m2" },
    ]);
  });
});

describe("escrita exclusiva modelId/dataSourceId", () => {
  it("buildViewDataLinkPatch: bind a modelo limpa dataSourceId", () => {
    const patch = buildViewDataLinkPatch({
      viewType: "kpi_view",
      dataSourceId: "",
      modelId: "m1",
      currentFrame: { x: 0, y: 0, w: 20, h: 10 },
      fitFrame: false,
    });
    expect(patch.modelId).toBe("m1");
    expect(patch.dataSourceId).toBeUndefined();
  });

  it("buildViewDataLinkPatch: bind a fonte limpa modelId", () => {
    const patch = buildViewDataLinkPatch({
      viewType: "kpi_view",
      dataSourceId: "src-1",
      currentFrame: { x: 0, y: 0, w: 20, h: 10 },
      fitFrame: false,
    });
    expect(patch.dataSourceId).toBe("src-1");
    expect(patch.modelId).toBeUndefined();
  });

  it("buildTextDataLinkPatch: modelId exclusivo", () => {
    const patch = buildTextDataLinkPatch({ dataSourceId: "", modelId: "m1" });
    expect(patch.modelId).toBe("m1");
    expect(patch.dataSourceId).toBeUndefined();
  });

  it("buildCanvasTableDataLinkPatch: modelId exclusivo no bloco", () => {
    const patch = buildCanvasTableDataLinkPatch({
      dataSourceId: "",
      modelId: "m1",
    });
    expect(patch.modelId).toBe("m1");
    expect(patch.dataSourceId).toBeUndefined();
  });

  it("célula: modelId limpa dataSourceId e vice-versa", () => {
    const table = makeCanvasTable();
    const withModel = applyCanvasTableCellModelId(table, { row: 1, col: 1 }, "m1");
    expect(withModel.cells[1]?.[1]?.modelId).toBe("m1");
    expect(withModel.cells[1]?.[1]?.dataSourceId).toBeUndefined();

    const backToSource = applyCanvasTableCellDataSourceId(
      withModel,
      { row: 1, col: 1 },
      "src-1",
    );
    expect(backToSource.cells[1]?.[1]?.dataSourceId).toBe("src-1");
    expect(backToSource.cells[1]?.[1]?.modelId).toBeUndefined();
  });
});

describe("Grade — resolução de target por célula", () => {
  it("resolveCanvasTableCellSourceId: modelId do bloco e da célula", () => {
    const table = makeCanvasTable({ modelId: "m1" });
    expect(resolveCanvasTableCellSourceId(table, table.cells[0]?.[0])).toBe("m1");

    const withCellModel = applyCanvasTableCellModelId(
      makeCanvasTable({ dataSourceId: "src-1" }),
      { row: 0, col: 0 },
      "m1",
    );
    expect(resolveCanvasTableCellSourceId(withCellModel, withCellModel.cells[0]?.[0])).toBe("m1");
    expect(resolveCanvasTableCellSourceId(withCellModel, withCellModel.cells[1]?.[0])).toBe("src-1");
  });

  it("collectCanvasTableSourceIds inclui modelos e fontes", () => {
    const table = applyCanvasTableCellModelId(
      makeCanvasTable({ modelId: "m1" }),
      { row: 1, col: 1 },
      "m2",
    );
    expect(collectCanvasTableSourceIds(table)).toEqual(["m1", "m2"]);
  });

  it("canvasTableHasDataBinding reconhece modelId-only", () => {
    expect(canvasTableHasDataBinding(makeCanvasTable({ modelId: "m1" }))).toBe(true);
    expect(canvasTableHasDataBinding(makeCanvasTable())).toBe(false);
  });
});

describe("texto/forma — binding model-aware", () => {
  it("textBlockHasDataBinding / linked target com modelId", () => {
    const block = { modelId: "m1" };
    expect(textBlockHasDataBinding(block)).toBe(true);
    expect(textBlockHasLinkedDataSource(block)).toBe(true);
  });
});

describe("visibilidade de palco — técnico vs visual vs oculto", () => {
  it("data_source ligado por modelId-target não esconde a fonte stale", () => {
    // Visual com modelId ativo + dataSourceId stale: a fonte legacy NÃO é consumida.
    const blocks = [
      makeSource("src-1"),
      makeView({ modelId: "m1", dataSourceId: "src-1" }),
    ];
    expect(shouldHideDataSourceOnStage("src-1", blocks)).toBe(false);
    expect(getLinkedDataSourceIds(blocks).has("src-1")).toBe(false);
    expect(getLinkedDataSourceIds(blocks).has("m1")).toBe(true);
  });

  it("data_source ligado por dataSourceId continua oculto (legacy)", () => {
    const blocks = [makeSource("src-1"), makeView({ dataSourceId: "src-1" })];
    expect(shouldHideDataSourceOnStage("src-1", blocks)).toBe(true);
    expect(listViewsLinkedToDataSource("src-1", blocks)).toHaveLength(1);
  });

  it("classificação semântica: data_source técnico ≠ visual oculto", () => {
    expect(isTechnicalDataBlockType("data_source")).toBe(true);
    expect(isRenderableBlockType("data_source")).toBe(false);
    expect(isRenderableBlockType("kpi_view")).toBe(true);
    // hidden é estado do usuário, não classificação de tipo.
    const hiddenView = makeView({ hidden: true });
    expect(isRenderableBlockType(hiddenView.type)).toBe(true);
  });
});

describe("normalizeDataModels — whitelist persistido (DM1)", () => {
  it("descarta artefatos de runtime e preserva contrato", () => {
    const models = normalizeDataModels([
      {
        id: "m1",
        label: "ROL",
        primaryInputId: "in-a",
        inputs: [
          {
            id: "in-a",
            operationId: "commercial.rol.summary",
            params: { period: "ano" },
            transform: { v: 2, steps: [] },
            resolved: { table: { rows: [] } },
            effectiveParams: { period: "mes" },
          },
        ],
        transform: { v: 1, steps: [{ op: "select" }] },
        fieldLabels: { rol: "ROL" },
        resolved: { kpiMetrics: [] },
        outputSchema: { fields: [] },
        runtimeErrors: ["boom"],
        rows: [{ a: 1 }],
      },
    ]);
    expect(models).toHaveLength(1);
    const model = models[0]!;
    expect(model.id).toBe("m1");
    expect(model.inputs[0]?.params).toEqual({ period: "ano" });
    expect(model.inputs[0]?.transform).toEqual({ v: 2, steps: [] });
    expect(model.fieldLabels).toEqual({ rol: "ROL" });
    expect("resolved" in model).toBe(false);
    expect("outputSchema" in model).toBe(false);
    expect("runtimeErrors" in model).toBe(false);
    expect("resolved" in (model.inputs[0] ?? {})).toBe(false);
    expect("effectiveParams" in (model.inputs[0] ?? {})).toBe(false);
  });

  it("rejeita modelo sem id/primaryInputId/inputs", () => {
    expect(
      normalizeDataModels([
        { id: "", primaryInputId: "a", inputs: [{ id: "a", operationId: "op" }] },
        { id: "x", primaryInputId: "", inputs: [{ id: "a", operationId: "op" }] },
        { id: "y", primaryInputId: "a", inputs: [] },
      ]),
    ).toHaveLength(0);
  });
});

describe("fingerprint + plano de refresh de modelos", () => {
  const model = makeModel();

  function fingerprintFor(config: ComunicadoConfig): string {
    return buildDataPreviewFingerprint(config);
  }

  it("definição alterada → refresh só do modelo afetado", () => {
    const prev = fingerprintFor({ dataModels: [model] });
    const changed = makeModel({ label: "ROL renomeado" });
    const next = fingerprintFor({ dataModels: [changed] });
    expect(planDataModelPreviewRefresh({
      previousFingerprint: prev,
      nextFingerprint: next,
      dataModels: [changed],
    })).toEqual(["m1"]);
  });

  it("filtro do slide → todos os modelos", () => {
    const models = [model, makeModel({ id: "m2" })];
    const prev = fingerprintFor({ dataModels: models });
    const next = fingerprintFor({
      dataModels: models,
      dataFilters: { filial: "02" } as ComunicadoConfig["dataFilters"],
    });
    expect(
      planDataModelPreviewRefresh({
        previousFingerprint: prev,
        nextFingerprint: next,
        dataModels: models,
      }).sort(),
    ).toEqual(["m1", "m2"]);
  });

  it("view link novo ligado a modelo → refresh do modelo (linkedResolved)", () => {
    const modelOnly: ComunicadoConfig = { dataModels: [model], blocks: [] };
    const prev = fingerprintFor(modelOnly);
    const next = fingerprintFor({
      dataModels: [model],
      blocks: [makeView({ modelId: "m1" })],
    });
    expect(
      planDataModelPreviewRefresh({
        previousFingerprint: prev,
        nextFingerprint: next,
        dataModels: [model],
      }),
    ).toEqual(["m1"]);
  });

  it("fingerprint igual → nada refetcha", () => {
    const fp = fingerprintFor({ dataModels: [model] });
    expect(
      planDataModelPreviewRefresh({
        previousFingerprint: fp,
        nextFingerprint: fp,
        dataModels: [model],
      }),
    ).toEqual([]);
  });
});
