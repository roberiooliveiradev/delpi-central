import { describe, expect, it } from "vitest";

import {
  effectiveKpiContextMode,
  resolveKpiOptionsWithAutoContext,
  suggestKpiVariantFromFrame,
} from "./resolveKpiAutoContext";
import { resolveKpiViewPresentation } from "./resolveKpiPresentation";
import { createKpiViewBlock } from "./comunicadoHelpers";

describe("kpi contextMode compatibility", () => {
  it("omitted contextMode ≡ off (legacy safe)", () => {
    expect(effectiveKpiContextMode({})).toBe("off");
    expect(effectiveKpiContextMode(null)).toBe("off");
    expect(effectiveKpiContextMode({ contextMode: "auto" })).toBe("auto");
    expect(effectiveKpiContextMode({ contextMode: "manual" })).toBe("manual");
  });

  it("suggests row for short frames and hero otherwise", () => {
    expect(suggestKpiVariantFromFrame({ h: 20 })).toBe("row");
    expect(suggestKpiVariantFromFrame({ h: 42 })).toBe("hero");
  });
});

describe("resolveKpiOptionsWithAutoContext", () => {
  it("positive: série ≥2 → sparkline + comparison previous", () => {
    const next = resolveKpiOptionsWithAutoContext(
      { contextMode: "auto", variant: "hero", showIcon: false },
      {
        kpi: { value: 110, label: "ROL" },
        chart: { points: [{ value: 90 }, { value: 100 }, { value: 110 }] },
      },
    );
    expect(next.showSparkline).toBe(true);
    expect(next.showProgress).toBe(false);
    expect(next.showComparison).toBe(true);
    expect(next.comparisonMode).toBe("previous");
  });

  it("sibling: target → progress + comparison target (scorecard)", () => {
    const next = resolveKpiOptionsWithAutoContext(
      { contextMode: "auto", variant: "scorecard", target: 100, showIcon: false },
      { kpi: { value: 95, label: "OTD" } },
    );
    expect(next.showProgress).toBe(true);
    expect(next.showSparkline).toBe(false);
    expect(next.showComparison).toBe(true);
    expect(next.comparisonMode).toBe("target");
  });

  it("negative: snapshot + auto → sem sparkline/progress", () => {
    const next = resolveKpiOptionsWithAutoContext(
      { contextMode: "auto", variant: "hero", showIcon: false },
      { kpi: { value: 42, label: "Qtd" } },
    );
    expect(next.showSparkline).toBe(false);
    expect(next.showProgress).toBe(false);
    expect(next.showComparison).toBe(false);
  });

  it("legacy off: não liga flags mesmo com série", () => {
    const next = resolveKpiOptionsWithAutoContext(
      { showSparkline: false, showComparison: false },
      {
        kpi: { value: 110 },
        chart: { points: [{ value: 1 }, { value: 2 }, { value: 3 }] },
      },
    );
    expect(next.showSparkline).toBe(false);
    expect(next.showComparison).toBe(false);
  });
});

describe("resolveKpiViewPresentation auto", () => {
  it("auto com série expõe sparkline sem flags manuais", () => {
    const presentation = resolveKpiViewPresentation(
      {
        kpi: { value: 85, label: "OEE" },
        chart: { points: [{ value: 70 }, { value: 75 }, { value: 85 }] },
      },
      { contextMode: "auto", variant: "hero", showIcon: false },
    );
    expect(presentation.sparklinePoints).toEqual([70, 75, 85]);
    expect(presentation.comparisonText).toMatch(/vs período/);
    expect(presentation.showIcon).toBe(false);
    expect(presentation.variant).toBe("hero");
  });

  it("GR-like: 1 hero + rows com série/meta sem flags manuais", () => {
    const hero = resolveKpiViewPresentation(
      {
        kpi: { value: 1_200_000, label: "ROL" },
        chart: { points: [{ value: 1_000_000 }, { value: 1_100_000 }, { value: 1_200_000 }] },
      },
      { contextMode: "auto", variant: "hero", showIcon: false, title: "ROL" },
    );
    expect(hero.variant).toBe("hero");
    expect(hero.sparklinePoints?.length).toBeGreaterThanOrEqual(2);
    expect(hero.comparisonText).toBeTruthy();
    expect(hero.showIcon).toBe(false);

    const row = resolveKpiViewPresentation(
      { kpi: { value: 96.5, label: "OTD" } },
      {
        contextMode: "auto",
        variant: "row",
        showIcon: false,
        title: "OTD",
        target: 95,
      },
    );
    expect(row.variant).toBe("row");
    expect(row.progressPct).toBeCloseTo((96.5 / 95) * 100);
    expect(row.sparklinePoints).toBeUndefined();
  });
});

describe("createKpiViewBlock defaults", () => {
  it("novos blocos nascem com contextMode auto e sem Gauge", () => {
    const block = createKpiViewBlock();
    expect(block.type).toBe("kpi_view");
    if (block.type !== "kpi_view") return;
    expect(block.kpiOptions?.contextMode).toBe("auto");
    expect(block.kpiOptions?.showIcon).toBe(false);
    expect(block.kpiOptions?.variant).toBeTruthy();
    expect(block.role).toBeTruthy();
  });

  it("frame baixo sugere variant row", () => {
    const block = createKpiViewBlock(undefined, { h: 18, w: 30 });
    if (block.type !== "kpi_view") return;
    expect(block.kpiOptions?.variant).toBe("row");
    expect(block.variant).toBe("row");
  });
});
