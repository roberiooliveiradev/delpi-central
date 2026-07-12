import { describe, expect, it } from "vitest";

import {
  borderRadiusPxToKpiCornerAdj,
  clampKpiPartFrame,
  deleteKpiPart,
  kpiCornerAdjToBorderRadiusPx,
  kpiOptionsToParts,
  kpiPartAllowsFrame,
  kpiPartAllowsResize,
  kpiPartCornerAdjustCssPosition,
  resolveKpiShapeChromePartRef,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  resizeKpiPartFrame,
  resolveKpiIconBoxStyle,
  resolveKpiPartFontSize,
  resolveKpiPartLayoutStyle,
  upsertKpiPartState,
} from "./kpiCardParts";
import {
  applyKpiElementVisibility,
  isKpiElementEnabled,
  isKpiElementOpenForPart,
  kpiElementPrimaryPartRef,
} from "./kpiElementCatalog";

describe("kpiCardParts adapters", () => {
  it("projeta options ↔ parts", () => {
    const parts = kpiOptionsToParts({
      title: "OEE",
      subtitle: "meta",
      showIcon: true,
      backgroundColor: "#fff",
      valueColor: "#111",
    });
    expect(parts.title?.content).toBe("OEE");
    expect(parts.hint?.content).toBe("meta");
    expect(parts.icon?.visible).toBe(true);
    expect(parts.card?.style?.fill).toBe("#fff");
    expect(parts.title?.style?.fontSize).toBe(14);
    expect(parts.value?.style?.fontSize).toBe(48);
    expect(parts.hint?.style?.fontSize).toBe(12);
    const back = partsToKpiOptions(parts);
    expect(back.title).toBe("OEE");
    expect(back.subtitle).toBe("meta");
    expect(back.showIcon).toBe(true);
  });

  it("deleteKpiPart oculta ícone e projeta options", () => {
    const result = deleteKpiPart(
      kpiOptionsToParts({ showIcon: true, title: "X" }),
      { kind: "icon" },
      { showIcon: true, title: "X" },
    );
    expect(result.parts.icon?.visible).toBe(false);
    expect(result.options.showIcon).toBe(false);
  });

  it("merge preserva overrides de parts", () => {
    const merged = mergeKpiPartsWithOptions(
      { title: { content: "Custom", visible: true } },
      { title: "Fonte", showIcon: false },
    );
    expect(merged.title?.content).toBe("Custom");
    expect(merged.icon?.visible).toBe(false);
  });

  it("sincroniza fill do card com backgroundColor (incl. cor custom)", () => {
    const parts = mergeKpiPartsWithOptions(
      { card: { style: { fill: "#089bdb" } } },
      { backgroundColor: "#ffffff" },
    );
    expect(parts.card?.style?.fill).toBe("#089bdb");
    expect(partsToKpiOptions(parts).backgroundColor).toBe("#089bdb");
  });
});

describe("kpiElementCatalog", () => {
  it("liga/desliga hint e ícone", () => {
    const off = applyKpiElementVisibility("kpiHint", false, { subtitle: "a" }, {});
    expect(off.options.subtitle).toBeUndefined();
    expect(isKpiElementEnabled("kpiHint", off.options, off.parts)).toBe(false);

    const iconOff = applyKpiElementVisibility("kpiIcon", false, { showIcon: true }, {});
    expect(iconOff.options.showIcon).toBe(false);
  });

  it("persiste título oculto em showTitle e parts (não volta ao render)", () => {
    const off = applyKpiElementVisibility(
      "kpiTitle",
      false,
      { title: "Taxa", showTitle: true },
      { title: { visible: true, content: "Taxa" } },
    );
    expect(off.options.showTitle).toBe(false);
    expect(off.parts.title?.visible).toBe(false);
    expect(isKpiElementEnabled("kpiTitle", off.options, off.parts)).toBe(false);

    const rematch = mergeKpiPartsWithOptions(off.parts, off.options);
    expect(rematch.title?.visible).toBe(false);
  });

  it("mapeia element ↔ part e foco", () => {
    expect(kpiElementPrimaryPartRef("kpiTitle")).toEqual({ kind: "title" });
    expect(isKpiElementOpenForPart("kpiTitle", { kind: "title" })).toBe(true);
    expect(isKpiElementOpenForPart("kpiValue", { kind: "title" })).toBe(false);
  });
})

describe("kpi icon layout", () => {
  it("resolveKpiIconBoxStyle aplica frame, cores e cantos", () => {
    const css = resolveKpiIconBoxStyle({
      frame: { x: 70, y: 5, w: 20, h: 30 },
      style: { fill: "#111", color: "#0af", stroke: "#fff", strokeWidth: 2, borderRadius: 10 },
    });
    expect(css.position).toBe("absolute");
    expect(css.left).toBe("70%");
    expect(css.width).toBe("20%");
    expect(css.background).toBe("#111");
    expect(css.color).toBe("#0af");
    expect(css.borderRadius).toBe("10px");
    expect(css.borderWidth).toBe("2px");
  });

  it("resolveKpiPartLayoutStyle aplica frame absoluto e raio", () => {
    const css = resolveKpiPartLayoutStyle({
      frame: { x: 10, y: 20, w: 40, h: 30 },
      style: { borderRadius: 8, fill: "#111" },
    });
    expect(css.position).toBe("absolute");
    expect(css.left).toBe("10%");
    expect(css.top).toBe("20%");
    expect(css.width).toBe("40%");
    expect(css.height).toBe("30%");
    expect(css.borderRadius).toBe("8px");
    expect(css.background).toBe("#111");
  });

  it("resolveKpiShapeChromePartRef mira a parte selecionada, não o card", () => {
    expect(resolveKpiShapeChromePartRef(null)).toEqual({ kind: "card" });
    expect(resolveKpiShapeChromePartRef({ kind: "value" })).toEqual({ kind: "value" });
    expect(resolveKpiShapeChromePartRef({ kind: "icon" })).toEqual({ kind: "icon" });
    expect(resolveKpiShapeChromePartRef({ kind: "card" })).toEqual({ kind: "card" });
  });

  it("kpiPartAllowsFrame cobre title/value/hint/icon", () => {
    expect(kpiPartAllowsFrame({ kind: "title" })).toBe(true);
    expect(kpiPartAllowsFrame({ kind: "value" })).toBe(true);
    expect(kpiPartAllowsFrame({ kind: "hint" })).toBe(true);
    expect(kpiPartAllowsFrame({ kind: "icon" })).toBe(true);
    expect(kpiPartAllowsFrame({ kind: "card" })).toBe(false);
  });

  it("resizeKpiPartFrame aplica delta pelos handles", () => {
    const origin = { x: 10, y: 20, w: 30, h: 40 };
    expect(resizeKpiPartFrame(origin, "e", 5, 0).w).toBe(35);
    expect(resizeKpiPartFrame(origin, "s", 0, 5).h).toBe(45);
    const nw = resizeKpiPartFrame(origin, "nw", -4, -3);
    expect(nw.x).toBe(6);
    expect(nw.y).toBe(17);
    expect(nw.w).toBe(34);
    expect(nw.h).toBe(43);
  });

  it("kpiPartCornerAdjustCssPosition acompanha o raio no track do topo", () => {
    const low = kpiPartCornerAdjustCssPosition(0, 100);
    const high = kpiPartCornerAdjustCssPosition(50, 100);
    expect(Number.parseFloat(low.left)).toBeLessThan(Number.parseFloat(high.left));
    expect(low.top).toBe("0%");
    expect(high.top).toBe("0%");
    expect(kpiCornerAdjToBorderRadiusPx(0.5, 80)).toBe(40);
    expect(borderRadiusPxToKpiCornerAdj(40, 80)).toBe(0.5);
  });

  it("kpiPartAllowsResize cobre partes internas e não o card", () => {
    expect(kpiPartAllowsResize({ kind: "value" })).toBe(true);
    expect(kpiPartAllowsResize({ kind: "card" })).toBe(false);
  });

  it("resolveKpiPartFontSize usa defaults canônicos quando sem fontSize", () => {
    expect(resolveKpiPartFontSize("title")).toBe(14);
    expect(resolveKpiPartFontSize("value")).toBe(48);
    expect(resolveKpiPartFontSize("hint")).toBe(12);
    expect(resolveKpiPartFontSize("value", { fontSize: 72 })).toBe(72);
  });

  it("upsertKpiPartState faz merge de frame e limpa com null", () => {
    const withFrame = upsertKpiPartState({}, { kind: "icon" }, { frame: { x: 10, y: 10, w: 12, h: 20 } });
    expect(clampKpiPartFrame(withFrame.icon!.frame!).x).toBe(10);
    const moved = upsertKpiPartState(withFrame, { kind: "icon" }, { frame: { x: 20 } });
    expect(moved.icon?.frame?.x).toBe(20);
    expect(moved.icon?.frame?.y).toBe(10);
    const cleared = upsertKpiPartState(moved, { kind: "icon" }, { frame: null, style: { iconSize: 48 } });
    expect(cleared.icon?.frame).toBeUndefined();
    expect(cleared.icon?.style?.iconSize).toBe(48);
  });
});
