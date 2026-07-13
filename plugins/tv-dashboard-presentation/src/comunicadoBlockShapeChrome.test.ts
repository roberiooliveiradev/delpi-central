import { describe, expect, it } from "vitest";

import {
  applyBlockShapeChromeAdjustment,
  applyBlockShapeChromeStyle,
  blockShapeChromeAdjustmentSpecs,
  blockSupportsShapeChromeHandles,
  resolveBlockSelectionBorderRadiusPx,
  resolveBlockShapeChromeAdjustmentValues,
  resolveBlockShapeChromeCornerPx,
  resolveBlockShapeChromeStyle,
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

  it("adj do handle usa o mesmo shortSidePx da conversão px↔adj", () => {
    const block = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const shortSide = 200;
    const withRadius = {
      ...block,
      ...applyBlockShapeChromeStyle(block, { borderRadius: 40 }),
    } as ComunicadoKpiViewBlock;
    const values = resolveBlockShapeChromeAdjustmentValues(withRadius, shortSide);
    expect(values[0]).toBeCloseTo(40 / shortSide, 5);
    const roundTrip = applyBlockShapeChromeAdjustment(withRadius, 0, values[0]!, shortSide);
    const next = { ...withRadius, ...roundTrip } as ComunicadoKpiViewBlock;
    expect(resolveBlockShapeChromeCornerPx(next)).toBe(40);
  });

  it("applyBlockShapeChromeStyle grava raio/borda no card do KPI (não só em style)", () => {
    const block = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const patch = applyBlockShapeChromeStyle(block, {
      borderRadius: 37,
      borderWidth: 2,
      borderColor: "#089bdb",
    });
    expect(patch).toBeTruthy();
    const next = { ...block, ...patch } as ComunicadoKpiViewBlock;
    const card = getKpiPartState(next.kpiParts, { kind: "card" });
    expect(card?.style?.borderRadius).toBe(37);
    expect(card?.style?.strokeWidth).toBe(2);
    expect(card?.style?.stroke).toBe("#089bdb");
    expect(resolveBlockShapeChromeCornerPx(next)).toBe(37);
    expect(resolveBlockShapeChromeStyle(next)?.borderRadius).toBe(37);
  });

  it("createTableViewBlock não grava maxRows a partir do picker", () => {
    const block = createTableViewBlock(5, 2) as ComunicadoTableViewBlock;
    expect(block.maxRows).toBeUndefined();
    expect(block.maxCols).toBeUndefined();
  });

  it("createTableViewBlock nasce com chrome Delpi (raio/sombra) na moldura", () => {
    const block = createTableViewBlock(3, 3) as ComunicadoTableViewBlock;
    expect(block.style?.boxShadow).toContain("rgba(15, 23, 42");
    expect(getTablePartState(block.tableParts, { kind: "frame" })?.style?.borderRadius).toBe(16);
    expect(getTablePartState(block.tableParts, { kind: "frame" })?.style?.boxShadow).toContain("rgba(15, 23, 42");
    expect(block.tableOptions?.showTitle).toBe(true);
  });
});
