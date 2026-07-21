import { describe, expect, it } from "vitest";

import type { ComunicadoBlock, ComunicadoDataResolved } from "./comunicadoTypes";
import {
  buildViewDataLinkPatch,
  buildViewFrameFitPatch,
  suggestViewFrameSize,
  syncDataViewBlocksWithResolved,
  viewHasProjectionConfigured,
} from "./syncViewDataLink";

const multiResolved: ComunicadoDataResolved = {
  kpi: { value: 30, label: "Quantidade" },
  kpiMetrics: [{ field: "quantidade", label: "Quantidade", value: 30 }],
  table: {
    columns: [
      { key: "periodo", label: "periodo" },
      { key: "oee_filial_01", label: "oee_filial_01" },
      { key: "oee_filial_02", label: "oee_filial_02" },
      { key: "quantidade", label: "Quantidade" },
    ],
    rows: [
      { periodo: "2026-01", oee_filial_01: 78.9, oee_filial_02: 73.8, quantidade: 1 },
      { periodo: "2026-02", oee_filial_01: 80, oee_filial_02: 74, quantidade: 1 },
    ],
  },
};

describe("syncViewDataLink", () => {
  it("materializa kpiProjection multi e amplia frame default", () => {
    const patch = buildViewDataLinkPatch({
      viewType: "kpi_view",
      dataSourceId: "src-1",
      resolved: multiResolved,
      fieldTypes: {
        periodo: "date",
        oee_filial_01: "number",
        oee_filial_02: "number",
        quantidade: "number",
      },
      currentFrame: { x: 8, y: 36, w: 12, h: 7 },
    });
    expect(patch.dataSourceId).toBe("src-1");
    expect(patch.kpiProjection?.metrics?.map((m) => m.field).sort()).toEqual([
      "oee_filial_01",
      "oee_filial_02",
      "quantidade",
    ]);
    expect(patch.frame?.w).toBeGreaterThan(12);
    expect(patch.frame?.h).toBeGreaterThanOrEqual(7);
  });

  it("não sobrescreve projection existente", () => {
    const patch = buildViewDataLinkPatch({
      viewType: "kpi_view",
      dataSourceId: "src-1",
      resolved: multiResolved,
      currentFrame: { x: 8, y: 36, w: 12, h: 7 },
      existing: {
        kpiProjection: {
          metrics: [{ field: "quantidade", label: "Q", visible: true, aggregation: "first" }],
        },
      },
    });
    expect(patch.kpiProjection).toBeUndefined();
  });

  it("suggestViewFrameSize cresce para 7 KPIs", () => {
    const next = suggestViewFrameSize("kpi_view", 7, { x: 8, y: 36, w: 12, h: 7 });
    expect(next.w).toBeGreaterThan(50);
    expect(next.h).toBeGreaterThan(20);
  });

  it("buildViewFrameFitPatch amplia KPI multi no frame default", () => {
    const block = {
      id: "k1",
      type: "kpi_view" as const,
      frame: { x: 8, y: 36, w: 12, h: 7 },
      style: { zIndex: 1 },
      kpiProjection: {
        metrics: [
          { field: "a", visible: true },
          { field: "b", visible: true },
          { field: "c", visible: true },
        ],
      },
    } as ComunicadoBlock;
    const patch = buildViewFrameFitPatch(block);
    expect(patch?.frame?.w).toBeGreaterThan(12);
  });

  it("syncDataViewBlocksWithResolved preenche projection quando resolved chega", () => {
    const blocks: ComunicadoBlock[] = [
      {
        id: "k1",
        type: "kpi_view",
        frame: { x: 8, y: 36, w: 12, h: 7 },
        style: { zIndex: 1 },
        dataSourceId: "src-1",
      } as ComunicadoBlock,
    ];
    expect(viewHasProjectionConfigured(blocks[0]!)).toBe(false);
    const { next, changedIds } = syncDataViewBlocksWithResolved(blocks, {
      "src-1": multiResolved,
    });
    expect(changedIds).toEqual(["k1"]);
    const kpi = next[0];
    expect(kpi?.type).toBe("kpi_view");
    if (kpi?.type !== "kpi_view") return;
    expect(kpi.kpiProjection?.metrics?.length).toBeGreaterThan(1);
    expect(kpi.frame.w).toBeGreaterThan(20);
  });

  it("sync também cobre chart_view e table_view", () => {
    const blocks: ComunicadoBlock[] = [
      {
        id: "c1",
        type: "chart_view",
        chartType: "line",
        frame: { x: 10, y: 28, w: 80, h: 45 },
        style: { zIndex: 1 },
        dataSourceId: "src-1",
      } as ComunicadoBlock,
      {
        id: "t1",
        type: "table_view",
        tablePreset: "grid",
        frame: { x: 5, y: 20, w: 40, h: 30 },
        style: { zIndex: 1 },
        dataSourceId: "src-1",
      } as ComunicadoBlock,
    ];
    const { next, changedIds } = syncDataViewBlocksWithResolved(blocks, {
      "src-1": multiResolved,
    });
    expect(changedIds).toContain("c1");
    expect(changedIds).toContain("t1");
    const chart = next.find((b) => b.type === "chart_view");
    const table = next.find((b) => b.type === "table_view");
    expect(chart && "chartProjection" in chart && chart.chartProjection?.series?.length).toBeGreaterThan(
      0,
    );
    expect(table && "tableProjection" in table && table.tableProjection?.columns?.length).toBeGreaterThan(
      0,
    );
  });
});
