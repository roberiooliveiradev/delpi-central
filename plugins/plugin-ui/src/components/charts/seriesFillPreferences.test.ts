import { describe, expect, it } from "vitest";

import {
  applySeriesFillPreferences,
  applySeriesViewPreferences,
  buildChartSeriesConfigItems,
  isSeriesTrendCapable,
  resetSeriesViewPreferences,
  resolveEffectiveShowTrend,
  resolveSeriesTrendEnabled,
} from "./seriesFillPreferences";
import type { MultiTypeSeriesSpec } from "./MultiTypeSeriesChart";

const BASE: MultiTypeSeriesSpec[] = [
  {
    dataKey: "rol_matrix",
    name: "Matriz",
    fill: "var(--chart-1)",
  },
  {
    dataKey: "rol_branch",
    name: "Filial",
    fill: "var(--chart-2)",
  },
  {
    dataKey: "rol_matrix_prior",
    name: "Matriz (ano ant.)",
    fill: "var(--chart-3)",
  },
];

describe("applySeriesFillPreferences", () => {
  it("mantém defaults quando não há overrides", () => {
    expect(applySeriesFillPreferences(BASE)).toEqual(BASE);
    expect(applySeriesFillPreferences(BASE, null)).toEqual(BASE);
    expect(applySeriesFillPreferences(BASE, {})).toEqual(BASE);
  });

  it("aplica override por dataKey e preserva demais campos", () => {
    const next = applySeriesFillPreferences(BASE, {
      rol_matrix: "#ff0000",
      unknown: "#000",
    });
    expect(next[0]).toEqual({
      dataKey: "rol_matrix",
      name: "Matriz",
      fill: "#ff0000",
    });
    expect(next[1].fill).toBe("var(--chart-2)");
    expect(next[2].fill).toBe("var(--chart-3)");
  });

  it("preserva axis e plotAs ao aplicar cor", () => {
    const dual: MultiTypeSeriesSpec[] = [
      {
        dataKey: "faturamento",
        name: "Faturamento",
        fill: "var(--chart-1)",
      },
      {
        dataKey: "quantidade",
        name: "Quantidade",
        fill: "var(--chart-2)",
        axis: "secondary",
        plotAs: "line",
      },
    ];
    const next = applySeriesFillPreferences(dual, { quantidade: "#ea580c" });
    expect(next[1]).toMatchObject({
      dataKey: "quantidade",
      fill: "#ea580c",
      axis: "secondary",
      plotAs: "line",
    });
  });

  it("ignora override vazio e não muta o array original", () => {
    const original = BASE.map((entry) => ({ ...entry }));
    const next = applySeriesFillPreferences(original, {
      rol_branch: "   ",
      rol_matrix_prior: "#64748b",
    });
    expect(next[1].fill).toBe("var(--chart-2)");
    expect(next[2].fill).toBe("#64748b");
    expect(original[2].fill).toBe("var(--chart-3)");
  });
});

describe("trend capability vs state", () => {
  it("séries temporais são capable por default, inclusive comparativas", () => {
    expect(BASE.every((entry) => isSeriesTrendCapable(entry))).toBe(true);
    const items = buildChartSeriesConfigItems(BASE);
    expect(items.map((entry) => entry.trendCapable)).toEqual([true, true, true]);
    expect(items.every((entry) => entry.trendEnabled === false)).toBe(true);
    expect(items.every((entry) => entry.trendApplyIncompleteBucket === true)).toBe(
      true,
    );
  });

  it("propaga opt-out de ponderação da spec comparativa", () => {
    const items = buildChartSeriesConfigItems([
      { dataKey: "faturamento", name: "Fat", fill: "#1" },
      {
        dataKey: "faturamento_prior",
        name: "Ano ant.",
        fill: "#2",
        trendApplyIncompleteBucket: false,
      },
    ]);
    expect(items[0].trendApplyIncompleteBucket).toBe(true);
    expect(items[1].trendApplyIncompleteBucket).toBe(false);
  });

  it("opt-out explícito desliga a capability", () => {
    expect(isSeriesTrendCapable({ trendCapable: false })).toBe(false);
    expect(
      resolveSeriesTrendEnabled("share", false, { share: true }),
    ).toBe(false);
  });

  it("showTrend legado não liga tendência no inspector", () => {
    const next = applySeriesViewPreferences(BASE, { showTrend: true });
    expect(next.every((entry) => entry.trendSource === false)).toBe(true);
    expect(resolveEffectiveShowTrend(BASE, undefined)).toBe(false);
  });

  it("default de qualquer série é tendência OFF", () => {
    expect(resolveSeriesTrendEnabled("rol_matrix", true)).toBe(false);
    expect(resolveSeriesTrendEnabled("rol_matrix", true, {})).toBe(false);
    expect(
      resolveSeriesTrendEnabled("rol_matrix", true, { rol_matrix: false }),
    ).toBe(false);
  });
});

describe("applySeriesViewPreferences", () => {
  it("série A ON não liga B; duas ON independentes; comparativa pode ligar", () => {
    const next = applySeriesViewPreferences(BASE, {
      showTrend: true,
      seriesTrend: { rol_matrix: true, rol_matrix_prior: true },
    });
    expect(next[0].trendSource).toBe(true);
    expect(next[1].trendSource).toBe(false);
    expect(next[2].trendSource).toBe(true);
  });

  it("A OFF não altera B", () => {
    const next = applySeriesViewPreferences(BASE, {
      seriesTrend: { rol_matrix: false, rol_branch: true },
    });
    expect(next[0].trendSource).toBe(false);
    expect(next[1].trendSource).toBe(true);
  });

  it("oculta por dataKey sem mutar origem e preserva seriesTrend no inspector", () => {
    const original = BASE.map((entry) => ({ ...entry }));
    const prefs = {
      hiddenSeries: { rol_branch: true },
      seriesTrend: { rol_branch: true, rol_matrix: true },
      seriesFills: { rol_matrix: "#ff0000" },
    };
    const next = applySeriesViewPreferences(BASE, prefs);
    expect(next.map((entry) => entry.dataKey)).toEqual([
      "rol_matrix",
      "rol_matrix_prior",
    ]);
    expect(next[0]).toMatchObject({
      dataKey: "rol_matrix",
      fill: "#ff0000",
      trendSource: true,
    });
    expect(prefs.seriesTrend.rol_branch).toBe(true);
    const items = buildChartSeriesConfigItems(BASE, prefs);
    expect(items.find((entry) => entry.dataKey === "rol_branch")).toMatchObject({
      visible: false,
      trendEnabled: true,
    });
    expect(original).toEqual(BASE);
  });

  it("aplica estilo de tendência só do dataKey", () => {
    const next = applySeriesViewPreferences(BASE, {
      seriesTrend: { rol_matrix: true, rol_branch: true },
      seriesTrendStyles: {
        rol_matrix: { dash: "solid", width: 4, color: "#111" },
      },
    });
    expect(next[0]).toMatchObject({
      trendStroke: "#111",
      trendLineStyle: "solid",
      trendStrokeWidth: 4,
    });
    expect(next[1].trendStroke).toBeUndefined();
    expect(next[1].trendLineStyle).toBeUndefined();
  });

  it("reset da série remove só aquele dataKey e volta tendência OFF", () => {
    const prev = {
      chartType: "column" as const,
      seriesFills: { rol_matrix: "#f00", rol_branch: "#0f0" },
      hiddenSeries: { rol_matrix: true },
      seriesTrend: { rol_matrix: true, rol_branch: false },
      seriesTrendStyles: { rol_matrix: { dash: "solid" as const } },
    };
    const next = resetSeriesViewPreferences(prev, "rol_matrix");
    expect(next.seriesFills).toEqual({ rol_branch: "#0f0" });
    expect(next.hiddenSeries).toBeUndefined();
    expect(next.seriesTrend).toEqual({ rol_branch: false });
    expect(next.seriesTrendStyles).toBeUndefined();
    expect(
      applySeriesViewPreferences(BASE, next).find(
        (entry) => entry.dataKey === "rol_matrix",
      )?.trendSource,
    ).toBe(false);
  });

  it("reset all limpa preferências de séries e não chartType", () => {
    const prev = {
      chartType: "line" as const,
      compareYears: 2,
      incompleteBucketMode: "weightByFraction" as const,
      seriesFills: { rol_matrix: "#f00" },
      hiddenSeries: { rol_branch: true },
      seriesTrend: { rol_matrix: true },
      seriesTrendStyles: { rol_matrix: { width: 4 } },
    };
    const next = resetSeriesViewPreferences(prev);
    expect(next.chartType).toBe("line");
    expect(next.compareYears).toBe(2);
    expect(next.incompleteBucketMode).toBe("weightByFraction");
    expect(next.seriesFills).toBeUndefined();
    expect(next.hiddenSeries).toBeUndefined();
    expect(next.seriesTrend).toBeUndefined();
    expect(next.seriesTrendStyles).toBeUndefined();
  });

  it("resolveEffectiveShowTrend ignora série oculta", () => {
    expect(
      resolveEffectiveShowTrend(
        BASE,
        { rol_branch: true },
        { rol_branch: true },
      ),
    ).toBe(false);
    expect(resolveEffectiveShowTrend(BASE, { rol_branch: true })).toBe(true);
  });
});
