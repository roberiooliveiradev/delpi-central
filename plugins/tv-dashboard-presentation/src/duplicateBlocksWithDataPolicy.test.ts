import { describe, expect, it } from "vitest";

import {
  duplicateBlocksWithDataPolicy,
  enrichClipboardWithLinkedDataSources,
  mustCloneDataSourcesForTarget,
  needsDataSourceDuplicateChoice,
  resolveBlockPasteDataPolicy,
} from "./duplicateBlocksWithDataPolicy";
import type { ComunicadoBlock } from "./comunicadoTypes";

const sourceBlock = (id: string): ComunicadoBlock =>
  ({
    id,
    type: "data_source",
    frame: { x: 10, y: 10, w: 20, h: 10 },
    dataBinding: { operationId: "get_oee", params: { dateRangePreset: "this_month" } },
  }) as ComunicadoBlock;

const chartView = (id: string, dataSourceId: string): ComunicadoBlock =>
  ({
    id,
    type: "chart_view",
    chartType: "bar",
    dataSourceId,
    frame: { x: 30, y: 10, w: 40, h: 30 },
  }) as ComunicadoBlock;

describe("duplicateBlocksWithDataPolicy", () => {
  it("needsDataSourceDuplicateChoice detecta visual com fonte", () => {
    expect(needsDataSourceDuplicateChoice([chartView("c1", "src-1")])).toBe(true);
    expect(
      needsDataSourceDuplicateChoice([
        { id: "t1", type: "text", content: "x", frame: { x: 0, y: 0, w: 10, h: 10 } },
      ]),
    ).toBe(false);
  });

  it("share_source mantém dataSourceId original", () => {
    const existing = [sourceBlock("src-1")];
    const result = duplicateBlocksWithDataPolicy(existing, [chartView("c1", "src-1")], "share_source");
    const copy = result.blocks.find((block) => block.id === result.pastedIds[0]);
    expect(copy && "dataSourceId" in copy ? copy.dataSourceId : null).toBe("src-1");
    expect(result.blocks.filter((block) => block.type === "data_source")).toHaveLength(1);
  });

  it("clone_source duplica fonte externa e remapeia visual", () => {
    const existing = [sourceBlock("src-1")];
    const result = duplicateBlocksWithDataPolicy(existing, [chartView("c1", "src-1")], "clone_source");
    const sources = result.blocks.filter((block) => block.type === "data_source");
    expect(sources).toHaveLength(2);
    const copy = result.blocks.find((block) => block.id === result.pastedIds[0]);
    expect(copy && "dataSourceId" in copy ? copy.dataSourceId : null).not.toBe("src-1");
    expect(copy && "dataSourceId" in copy ? copy.dataSourceId : null).toBe(sources[1]?.id);
  });

  it("clone_source cria fonte a partir do payload quando o slide alvo não tem a fonte", () => {
    const src = sourceBlock("src-1");
    const chart = chartView("c1", "src-1");
    const payload = enrichClipboardWithLinkedDataSources([chart], [src, chart]);
    expect(payload.some((block) => block.type === "data_source")).toBe(true);

    const otherSlide: ComunicadoBlock[] = [];
    expect(mustCloneDataSourcesForTarget(payload, otherSlide)).toBe(true);

    const result = duplicateBlocksWithDataPolicy(otherSlide, payload, "clone_source");
    const sources = result.blocks.filter((block) => block.type === "data_source");
    expect(sources).toHaveLength(1);
    const pastedChart = result.blocks.find(
      (block) => block.type === "chart_view" && result.pastedIds.includes(block.id),
    );
    expect(pastedChart && "dataSourceId" in pastedChart ? pastedChart.dataSourceId : null).toBe(
      sources[0]?.id,
    );
    expect(sources[0]?.id).not.toBe("src-1");
  });

  it("share_source com payload enriquecido não cria fonte órfã no mesmo slide", () => {
    const src = sourceBlock("src-1");
    const chart = chartView("c1", "src-1");
    const payload = enrichClipboardWithLinkedDataSources([chart], [src, chart]);
    const result = duplicateBlocksWithDataPolicy([src, chart], payload, "share_source");
    expect(result.blocks.filter((block) => block.type === "data_source")).toHaveLength(1);
    const copy = result.blocks.find((block) => block.id === result.pastedIds[0]);
    expect(copy && "dataSourceId" in copy ? copy.dataSourceId : null).toBe("src-1");
  });

  it("resolveBlockPasteDataPolicy força clone cross-slide e pergunta no mesmo slide", () => {
    const src = sourceBlock("src-1");
    const chart = chartView("c1", "src-1");
    const sameSlide = resolveBlockPasteDataPolicy({
      incoming: [chart],
      targetBlocks: [src, chart],
    });
    expect(sameSlide.requiresUserChoice).toBe(true);
    expect(sameSlide.policy).toBe("share_source");

    const cross = resolveBlockPasteDataPolicy({
      incoming: enrichClipboardWithLinkedDataSources([chart], [src, chart]),
      targetBlocks: [],
    });
    expect(cross.requiresUserChoice).toBe(false);
    expect(cross.policy).toBe("clone_source");
  });

  it("duplica grupo com novo groupId (não entra no grupo da origem)", () => {
    const a = {
      id: "a",
      type: "text" as const,
      content: "A",
      frame: { x: 10, y: 10, w: 20, h: 10 },
      groupId: "grp_orig",
    };
    const b = {
      id: "b",
      type: "text" as const,
      content: "B",
      frame: { x: 40, y: 10, w: 20, h: 10 },
      groupId: "grp_orig",
    };
    const result = duplicateBlocksWithDataPolicy([a, b], [a, b], "share_source");
    const pasted = result.blocks.filter((block) => result.pastedIds.includes(block.id));
    expect(pasted).toHaveLength(2);
    expect(pasted[0]?.groupId).toBeTruthy();
    expect(pasted[0]?.groupId).not.toBe("grp_orig");
    expect(pasted[1]?.groupId).toBe(pasted[0]?.groupId);
    expect(result.blocks.find((block) => block.id === "a")?.groupId).toBe("grp_orig");
  });

  it("clone_source remapeia tabela, KPI, texto e grade para a fonte clonada", () => {
    const source = sourceBlock("src-1");
    const frame = { x: 10, y: 10, w: 20, h: 10 };
    const views = [
      { id: "table", type: "table_view" as const, dataSourceId: "src-1", frame },
      { id: "kpi", type: "kpi_view" as const, dataSourceId: "src-1", frame },
      { id: "label", type: "text" as const, content: "OTD", dataSourceId: "src-1", frame },
      { id: "grid", type: "canvas_table" as const, dataSourceId: "src-1", frame, cells: [] },
    ];
    const result = duplicateBlocksWithDataPolicy([source], views, "clone_source");
    const pasted = result.blocks.filter((block) => result.pastedIds.includes(block.id));
    const clonedSource = result.blocks.find(
      (block) => block.type === "data_source" && block.id !== "src-1",
    );
    expect(clonedSource?.id).toBeTruthy();
    expect(clonedSource?.id).not.toBe("src-1");
    for (const block of pasted) {
      expect("dataSourceId" in block ? block.dataSourceId : null).toBe(clonedSource?.id);
    }
    expect(result.blocks.find((block) => block.id === "src-1")?.type).toBe("data_source");
  });

  it("conector sem ponta permanece vazio e a ponta ligada acompanha a cópia", () => {
    const frame = { x: 10, y: 10, w: 20, h: 10 };
    const origin = {
      id: "origin",
      type: "shape" as const,
      shape: "rectangle" as const,
      content: "",
      frame,
    };
    const arrow = {
      id: "arrow",
      type: "shape" as const,
      shape: "line" as const,
      content: "",
      frame,
      connector: { fromBlockId: "origin", toBlockId: undefined },
    };
    const result = duplicateBlocksWithDataPolicy([], [origin, arrow], "share_source");
    const pastedArrow = result.blocks.find(
      (block) => result.pastedIds.includes(block.id) && block.type === "shape" && block.shape === "line",
    );
    const pastedOrigin = result.blocks.find(
      (block) => result.pastedIds.includes(block.id) && block.id !== pastedArrow?.id,
    );
    expect(pastedArrow && pastedArrow.type === "shape" ? pastedArrow.connector?.fromBlockId : null).toBe(
      pastedOrigin?.id,
    );
    expect(pastedArrow && pastedArrow.type === "shape" ? pastedArrow.connector?.toBlockId : "missing").toBeUndefined();
  });

  it("ícone sem fonte não cria data_source", () => {
    const icon = {
      id: "icon-1",
      type: "icon" as const,
      iconName: "Star",
      frame: { x: 0, y: 0, w: 8, h: 8 },
    };
    const result = duplicateBlocksWithDataPolicy([], [icon], "clone_source");
    expect(result.blocks.some((block) => block.type === "data_source")).toBe(false);
  });
});
