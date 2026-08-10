import { describe, expect, it } from "vitest";

import { shapeBlockAllowsResize } from "./comunicadoShapeGeometry";
import {
  EFFICIENCY_PIN_OPERATION_ID,
  applySharedDataSourceToUnlinkedEfficiencyPins,
  buildEfficiencyPinInfoBlock,
  classifyEfficiencyPinPct,
  ensureEfficiencyPinResizableFrame,
  findSharedEfficiencyPinDataSourceId,
  isEfficiencyPinShapeKind,
  listWorkCentersFromResolved,
  normalizeEfficiencyPinBinding,
  resolveEfficiencyPinInfoMode,
  resolveEfficiencyPinRole,
  resolveEfficiencyPinState,
} from "./efficiencyPin";

describe("efficiencyPin", () => {
  it("reconhece o kind efficiency-pin", () => {
    expect(isEfficiencyPinShapeKind("efficiency-pin")).toBe(true);
    expect(isEfficiencyPinShapeKind("point")).toBe(false);
  });

  it("classifica faixas alinhadas à eficiência fabril", () => {
    expect(classifyEfficiencyPinPct(110)).toBe("good");
    expect(classifyEfficiencyPinPct(95)).toBe("good");
    expect(classifyEfficiencyPinPct(70)).toBe("warn");
    expect(classifyEfficiencyPinPct(40)).toBe("bad");
    expect(classifyEfficiencyPinPct(250)).toBe("verify");
    expect(classifyEfficiencyPinPct(null)).toBe("unknown");
  });

  it("resolve cor e % pelo work_center na tabela", () => {
    const state = resolveEfficiencyPinState({
      efficiencyPin: { workCenter: "CT-01" },
      resolved: {
        table: {
          rows: [
            { work_center: "CT-02", efficiency_pct: 40 },
            { work_center: "CT-01", efficiency_pct: 102.5, appointment_count: 3 },
          ],
        },
      },
    });
    expect(state.status).toBe("good");
    expect(state.efficiencyPct).toBe(102.5);
    expect(state.color).toBe("#22c55e");
    expect(state.label).toBe("CT-01");
  });

  it("lista CTs únicos ordenados e normaliza binding", () => {
    expect(
      listWorkCentersFromResolved({
        table: {
          rows: [
            { work_center: "B", efficiency_pct: 10 },
            { work_center: "A", efficiency_pct: 90 },
            { work_center: "B", efficiency_pct: 20 },
          ],
        },
      }),
    ).toEqual(["A", "B"]);

    expect(
      normalizeEfficiencyPinBinding({
        workCenter: " CT-99 ",
        showLabel: false,
        infoMode: "detached",
        role: "info",
        linkedBlockId: "pin-1",
        bands: { goodMinPct: 100, warnMinPct: 60 },
      }),
    ).toEqual({
      workCenter: "CT-99",
      showLabel: false,
      infoMode: "detached",
      role: "info",
      linkedBlockId: "pin-1",
      bands: { goodMinPct: 100, warnMinPct: 60 },
    });
  });

  it("cria bloco info destacado ao lado do pin", () => {
    const pin = {
      id: "pin-a",
      type: "shape" as const,
      shape: "efficiency-pin" as const,
      frame: { x: 10, y: 20, w: 12, h: 14 },
      dataSourceId: "src-1",
      efficiencyPin: { workCenter: "CT-01", role: "pin" as const, infoMode: "attached" as const },
    };
    const info = buildEfficiencyPinInfoBlock(pin);
    expect(info.shape).toBe("efficiency-pin");
    expect(resolveEfficiencyPinRole(info.efficiencyPin)).toBe("info");
    expect(info.efficiencyPin?.linkedBlockId).toBe("pin-a");
    expect(info.dataSourceId).toBe("src-1");
    expect(info.frame.x).toBeGreaterThan(pin.frame.x);
    expect(resolveEfficiencyPinInfoMode({ showLabel: false })).toBe("hidden");
    expect(resolveEfficiencyPinInfoMode({ infoMode: "detached" })).toBe("detached");
  });

  it("migra frame w/h≈0 para área redimensionável centrada", () => {
    const block = {
      id: "pin-1",
      type: "shape" as const,
      shape: "efficiency-pin" as const,
      frame: { x: 50, y: 40, w: 0, h: 0 },
      style: {},
      content: "",
      efficiencyPin: { role: "pin" as const, infoMode: "attached" as const },
      vertices: [{ x: 50, y: 40 }],
    };
    const fixed = ensureEfficiencyPinResizableFrame(block, { x: 40, y: 35, w: 10, h: 10 });
    expect(fixed.frame.w).toBeGreaterThanOrEqual(4);
    expect(fixed.frame.h).toBeGreaterThanOrEqual(4);
    expect(fixed.frame.x + fixed.frame.w / 2).toBeCloseTo(50, 5);
    expect(fixed.frame.y + fixed.frame.h / 2).toBeCloseTo(40, 5);
    expect(fixed.vertices).toBeUndefined();
    expect(shapeBlockAllowsResize(fixed)).toBe(true);
  });

  it("reutiliza uma fonte de eficiência entre vários pins", () => {
    const source = {
      id: "src-eff",
      type: "data_source" as const,
      frame: { x: 0, y: 0, w: 10, h: 10 },
      style: {},
      dataBinding: { operationId: EFFICIENCY_PIN_OPERATION_ID },
    };
    const pinA = {
      id: "pin-a",
      type: "shape" as const,
      shape: "efficiency-pin" as const,
      frame: { x: 10, y: 10, w: 8, h: 8 },
      style: {},
      content: "",
      dataSourceId: "src-eff",
      efficiencyPin: { workCenter: "CT-01", role: "pin" as const },
    };
    const pinB = {
      id: "pin-b",
      type: "shape" as const,
      shape: "efficiency-pin" as const,
      frame: { x: 30, y: 10, w: 8, h: 8 },
      style: {},
      content: "",
      efficiencyPin: { workCenter: "CT-02", role: "pin" as const },
    };
    expect(findSharedEfficiencyPinDataSourceId([source, pinA, pinB])).toBe("src-eff");
    const linked = applySharedDataSourceToUnlinkedEfficiencyPins([source, pinA, pinB], "src-eff");
    expect(linked.find((block) => block.id === "pin-b")).toMatchObject({ dataSourceId: "src-eff" });
    expect(linked.find((block) => block.id === "pin-a")).toMatchObject({ dataSourceId: "src-eff" });
  });
});
