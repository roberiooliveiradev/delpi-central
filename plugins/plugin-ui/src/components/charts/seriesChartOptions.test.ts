import { describe, expect, it } from "vitest";

import {
  DEFAULT_SERIES_CHART_OPTIONS,
  SERIES_CHART_CHROME_VERSION,
  formatSeriesChartCategoryLabel,
  formatSeriesChartValue,
  migrateSeriesChartOptionsOnLoad,
  resolveSeriesCategoryColor,
  resolveSeriesChartDisplayOptions,
  resolveSeriesChartLegendLayout,
  resolveSeriesChartLegendSort,
  resolveSeriesChartTicks,
  resolveSeriesChartValueDomain,
  resolveValueScaleColor,
  resolveGoalThresholdColor,
  GOAL_SCALE_COLORS,
  seriesValueExtent,
} from "./seriesChartOptions";

const RAG_RAMP = ["#15803d", "#2563eb", "#eab308", "#ea580c", "#be123c"] as const;

describe("seriesChartOptions — títulos de eixo", () => {
  it("liga títulos de eixo por padrão", () => {
    expect(DEFAULT_SERIES_CHART_OPTIONS.showXAxisTitle).toBe(true);
    expect(DEFAULT_SERIES_CHART_OPTIONS.showYAxisTitle).toBe(true);
    expect(DEFAULT_SERIES_CHART_OPTIONS.legendLayout).toBe("auto");
    expect(DEFAULT_SERIES_CHART_OPTIONS.legendSort).toBe("auto");
    expect(DEFAULT_SERIES_CHART_OPTIONS.chromeVersion).toBe(SERIES_CHART_CHROME_VERSION);
  });

  it("resolveSeriesChartDisplayOptions preenche eixos com dados da rota (como o título)", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      {},
      {
        label: "OEE — série temporal",
        kpi: { label: "OEE" },
        table: {
          columns: [
            { key: "periodo", label: "Período" },
            { key: "value", label: "OEE %" },
          ],
        },
      },
    );
    expect(resolved.title).toBe("OEE — série temporal");
    expect(resolved.xAxisTitle).toBe("Período");
    expect(resolved.yAxisTitle).toBe("OEE %");
    expect(resolved.showXAxisTitle).toBe(true);
    expect(resolved.showYAxisTitle).toBe(true);
  });

  it("resolveSeriesChartDisplayOptions não infere formato — escolha do usuário", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      { valueFormat: "auto" },
      {
        label: "Relatório operacional — Refugos rankings",
        table: {
          columns: [
            { key: "code", label: "Código" },
            { key: "value", label: "Valor (R$)" },
          ],
        },
      },
    );
    expect(resolved.valueFormat).toBe("auto");
  });

  it("resolveSeriesChartDisplayOptions preserva formato explícito do usuário", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      { valueFormat: "currency" },
      {
        table: {
          columns: [
            { key: "code", label: "Código" },
            { key: "sharePct", label: "Participação (%)" },
          ],
        },
      },
    );
    expect(resolved.valueFormat).toBe("currency");
  });

  it("resolveSeriesChartDisplayOptions preserva override explícito dos eixos", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      { xAxisTitle: "Mês", yAxisTitle: "Índice", showXAxisTitle: false },
      {
        label: "OTD — série temporal",
        table: { columns: [{ key: "periodo", label: "Período" }] },
      },
    );
    expect(resolved.xAxisTitle).toBe("Mês");
    expect(resolved.yAxisTitle).toBe("Índice");
    expect(resolved.showXAxisTitle).toBe(false);
  });

  it("migrateSeriesChartOptionsOnLoad liga eixos em bloco legado sem chromeVersion", () => {
    const migrated = migrateSeriesChartOptionsOnLoad({
      showXAxisTitle: false,
      showYAxisTitle: false,
    });
    expect(migrated.showXAxisTitle).toBe(true);
    expect(migrated.showYAxisTitle).toBe(true);
    expect(migrated.chromeVersion).toBe(SERIES_CHART_CHROME_VERSION);
  });

  it("migrateSeriesChartOptionsOnLoad preserva eixos desligados após chromeVersion atual", () => {
    const migrated = migrateSeriesChartOptionsOnLoad({
      showXAxisTitle: false,
      showYAxisTitle: false,
      chromeVersion: SERIES_CHART_CHROME_VERSION,
    });
    expect(migrated.showXAxisTitle).toBe(false);
    expect(migrated.showYAxisTitle).toBe(false);
  });

  it("migrate v2 zera categoryPaddingPercent legado (extremos no eixo X)", () => {
    const migrated = migrateSeriesChartOptionsOnLoad({
      categoryPaddingPercent: 6,
      chromeVersion: 1,
    });
    expect(migrated.categoryPaddingPercent).toBe(0);
    expect(migrated.chromeVersion).toBe(SERIES_CHART_CHROME_VERSION);
  });
});

describe("formatSeriesChartValue / category label", () => {
  it("compact formata em notação curta pt-BR", () => {
    const formatted = formatSeriesChartValue(28000, "compact");
    expect(formatted.toLowerCase()).toMatch(/28/);
    expect(formatted.toLowerCase()).toMatch(/mil|k/);
  });

  it("autoDate encurta ISO date", () => {
    expect(formatSeriesChartCategoryLabel("2026-07-01", "autoDate")).toBe("01 Jul");
  });

  it("month usa abreviação pt-BR fixa (não depende de ICU)", () => {
    expect(formatSeriesChartCategoryLabel("2026-02", "month")).toBe("Fev. de 2026");
    expect(formatSeriesChartCategoryLabel("2026-05", "month")).toBe("Mai. de 2026");
  });

  it("raw localiza abreviações EN remanescentes (cache antigo)", () => {
    expect(formatSeriesChartCategoryLabel("Feb. de 26", "raw")).toBe("Fev. de 26");
    expect(formatSeriesChartCategoryLabel("Aug. de 25", "raw")).toBe("Ago. de 25");
  });

  it("defaults de label format preservam playlists antigas", () => {
    expect(DEFAULT_SERIES_CHART_OPTIONS.categoryLabelRotation).toBe("auto");
    expect(DEFAULT_SERIES_CHART_OPTIONS.categoryLabelOverflow).toBe("skip");
    expect(DEFAULT_SERIES_CHART_OPTIONS.categoryLabelFormat).toBe("raw");
  });
});

describe("resolveSeriesChartTicks — domínio cobre dataMax", () => {
  it("não trunca economia ~875 com piso ~100 (regressão clip no teto)", () => {
    const ticks = resolveSeriesChartTicks(100, 875);
    expect(ticks[0]!).toBeLessThanOrEqual(100);
    expect(ticks[ticks.length - 1]!).toBeGreaterThanOrEqual(875);
  });

  it("cobre max quando cai entre ticks nice", () => {
    const ticks = resolveSeriesChartTicks(0, 875);
    expect(ticks[ticks.length - 1]!).toBeGreaterThanOrEqual(875);
  });

  it("reserva headroom quando max já é tick nice (evita área achatada no topo)", () => {
    const ticks = resolveSeriesChartTicks(0, 800);
    expect(ticks[0]).toBe(0);
    expect(ticks[ticks.length - 1]!).toBeGreaterThan(800);
  });

  it("Transforma+ ~28k: teto do eixo acima do pico (não cola no clip)", () => {
    const ticks = resolveSeriesChartTicks(0, 28_000);
    expect(ticks).toContain(0);
    expect(ticks).toContain(28_000);
    expect(ticks[ticks.length - 1]!).toBeGreaterThan(28_000);
  });

  it("pico quase no teto nice (27,5k→28k) ainda ganha headroom", () => {
    const ticks = resolveSeriesChartTicks(0, 27_500);
    expect(ticks[ticks.length - 1]!).toBeGreaterThan(28_000);
  });
});

describe("resolveSeriesChartValueDomain", () => {
  it("dados ≥ 0 incluem zero (14 e 16 não colam o menor no baseline)", () => {
    expect(resolveSeriesChartValueDomain(14, 16)).toEqual({ min: 0, max: 16 });
  });

  it("dados ≤ 0 incluem zero no teto", () => {
    expect(resolveSeriesChartValueDomain(-16, -14)).toEqual({ min: -16, max: 0 });
  });

  it("domínio que cruza zero permanece intacto", () => {
    expect(resolveSeriesChartValueDomain(-5, 10)).toEqual({ min: -5, max: 10 });
  });
});

describe("resolveValueScaleColor — colorir por valor", () => {
  it("high_is_bad: valor alto → vermelho (fim da rampa Melhor→pior)", () => {
    expect(
      resolveValueScaleColor({
        value: 100,
        min: 0,
        max: 100,
        colors: RAG_RAMP,
        polarity: "high_is_bad",
      }),
    ).toBe("#be123c");
  });

  it("high_is_good: valor alto → verde (início da rampa)", () => {
    expect(
      resolveValueScaleColor({
        value: 100,
        min: 0,
        max: 100,
        colors: RAG_RAMP,
        polarity: "high_is_good",
      }),
    ).toBe("#15803d");
  });

  it("high_is_bad: valor baixo → verde", () => {
    expect(
      resolveValueScaleColor({
        value: 0,
        min: 0,
        max: 100,
        colors: RAG_RAMP,
        polarity: "high_is_bad",
      }),
    ).toBe("#15803d");
  });

  it("mode off equivalente: resolveSeriesCategoryColor usa índice", () => {
    expect(resolveSeriesCategoryColor(0, "#089bdb", [...RAG_RAMP])).toBe("#15803d");
    expect(resolveSeriesCategoryColor(4, "#089bdb", [...RAG_RAMP])).toBe("#be123c");
  });

  it("seriesValueExtent ignora null/NaN", () => {
    expect(seriesValueExtent([10, null, 40, Number.NaN, 5])).toEqual({ min: 5, max: 40 });
  });
});

describe("resolveGoalThresholdColor — colorir pela meta", () => {
  it("high_is_good: ≥ meta verde; faixa 5% laranja; abaixo vermelho", () => {
    expect(
      resolveGoalThresholdColor({ value: 100, goal: 100, polarity: "high_is_good" }),
    ).toBe(GOAL_SCALE_COLORS.good);
    expect(
      resolveGoalThresholdColor({ value: 96, goal: 100, polarity: "high_is_good" }),
    ).toBe(GOAL_SCALE_COLORS.warn);
    expect(
      resolveGoalThresholdColor({ value: 90, goal: 100, polarity: "high_is_good" }),
    ).toBe(GOAL_SCALE_COLORS.bad);
  });

  it("high_is_bad: ≤ meta verde; faixa 5% acima laranja; acima vermelho", () => {
    expect(
      resolveGoalThresholdColor({ value: 10, goal: 10, polarity: "high_is_bad" }),
    ).toBe(GOAL_SCALE_COLORS.good);
    expect(
      resolveGoalThresholdColor({ value: 10.4, goal: 10, polarity: "high_is_bad" }),
    ).toBe(GOAL_SCALE_COLORS.warn);
    expect(
      resolveGoalThresholdColor({ value: 12, goal: 10, polarity: "high_is_bad" }),
    ).toBe(GOAL_SCALE_COLORS.bad);
  });

  it("meta inválida usa fallback", () => {
    expect(
      resolveGoalThresholdColor({
        value: 50,
        goal: Number.NaN,
        fallbackColor: "#089bdb",
      }),
    ).toBe("#089bdb");
  });
});

describe("legenda — layout e ordenação automáticos", () => {
  it("auto: laterais em coluna; top/bottom em linha com poucas categorias", () => {
    expect(
      resolveSeriesChartLegendLayout({
        position: "right",
        layout: "auto",
        itemCount: 5,
        usesCategoryLegend: true,
      }),
    ).toBe("column");
    expect(
      resolveSeriesChartLegendLayout({
        position: "bottom",
        layout: "auto",
        itemCount: 2,
        usesCategoryLegend: true,
      }),
    ).toBe("row");
  });

  it("auto: top/bottom em coluna com ≥4 categorias (padrão de ajuste)", () => {
    expect(
      resolveSeriesChartLegendLayout({
        position: "bottom",
        layout: "auto",
        itemCount: 5,
        usesCategoryLegend: true,
      }),
    ).toBe("column");
  });

  it("força linha mesmo à direita", () => {
    expect(
      resolveSeriesChartLegendLayout({
        position: "right",
        layout: "row",
        itemCount: 5,
        usesCategoryLegend: true,
      }),
    ).toBe("row");
  });

  it("auto: pizza/funil ordenam por valor ↓", () => {
    expect(
      resolveSeriesChartLegendSort({
        chartType: "pie",
        sort: "auto",
        usesCategoryLegend: true,
      }),
    ).toBe("valueDesc");
    expect(
      resolveSeriesChartLegendSort({
        chartType: "line",
        sort: "auto",
        usesCategoryLegend: false,
      }),
    ).toBe("data");
  });
});
