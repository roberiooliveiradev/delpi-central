import { describe, expect, it } from "vitest";

import {
  applyBlockShapeChromeAdjustment,
  blockShapeChromeAdjustmentSpecs,
  blockSupportsShapeChromeHandles,
  resolveBlockSelectionBorderRadiusPx,
  resolveBlockShapeChromeCornerPx,
} from "./comunicadoBlockShapeChrome";
import {
  createChartViewBlock,
  createKpiViewBlock,
  createShapeBlock,
  createTableViewBlock,
} from "./comunicadoHelpers";
import { getKpiPartState } from "./comunicadoKpiParts";
import { getTablePartState } from "./comunicadoTableParts";
import type { ComunicadoKpiViewBlock, ComunicadoTableViewBlock } from "./comunicadoTypes";

describe("comunicadoBlockShapeChrome", () => {
  it("herda handles de cantos em KPI, tabela e chart (além da forma)", () => {
    expect(blockSupportsShapeChromeHandles(createShapeBlock("rectangle"))).toBe(true);
    expect(blockSupportsShapeChromeHandles(createKpiViewBlock())).toBe(true);
    expect(blockSupportsShapeChromeHandles(createTableViewBlock(3, 3))).toBe(true);
    expect(blockSupportsShapeChromeHandles(createChartViewBlock("line"))).toBe(true);
    expect(blockShapeChromeAdjustmentSpecs(createKpiViewBlock()).some((s) => s.id === "corner")).toBe(
      true,
    );
  });

  it("aplica ajuste de canto no card do KPI", () => {
    const block = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const patch = applyBlockShapeChromeAdjustment(block, 0, 0.25, 80);
    expect(patch).toBeTruthy();
    const next = { ...block, ...patch } as ComunicadoKpiViewBlock;
    expect(resolveBlockShapeChromeCornerPx(next)).toBe(20);
    expect(getKpiPartState(next.kpiParts, { kind: "card" })?.style?.borderRadius).toBe(20);
  });

  it("aplica ajuste de canto na moldura da tabela (tableParts.frame)", () => {
    const block = createTableViewBlock(3, 3) as ComunicadoTableViewBlock;
    const patch = applyBlockShapeChromeAdjustment(block, 0, 0.125, 64);
    expect(patch?.style?.borderRadius).toBe(8);
    const next = { ...block, ...patch } as ComunicadoTableViewBlock;
    expect(getTablePartState(next.tableParts, { kind: "frame" })?.style?.borderRadius).toBe(8);
    expect(resolveBlockShapeChromeCornerPx(next)).toBe(8);
  });

  it("alinhar outline de seleção ao raio do chrome", () => {
    const base = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const patch = applyBlockShapeChromeAdjustment(base, 0, 14 / 64, 64);
    const kpi = { ...base, ...patch } as ComunicadoKpiViewBlock;
    expect(resolveBlockSelectionBorderRadiusPx(kpi)).toBe(14);
    expect(resolveBlockSelectionBorderRadiusPx(createShapeBlock("point"))).toBeUndefined();
  });

  it("createTableViewBlock não grava maxRows a partir do picker", () => {
    const block = createTableViewBlock(5, 2) as ComunicadoTableViewBlock;
    expect(block.maxRows).toBeUndefined();
    expect(block.maxCols).toBeUndefined();
  });
});
