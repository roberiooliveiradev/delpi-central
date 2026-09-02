import { describe, expect, it } from "vitest";

import {
  applyAdaptiveChartLabels,
  boundsForHistoryPreset,
  datetimeLocalToIso,
  downsampleChartPoints,
  formatChartTick,
  resolveChartTickGranularity,
  resolveDefaultHistoryPreset,
  resolveHistoryChartPageSize,
  resolveHistoryChartSampleIntervalMs,
  HISTORY_CHART_SAMPLE_INTERVAL_MS_MAX,
  toDatetimeLocalValue,
} from "./historyTimeRange";

describe("historyTimeRange", () => {
  it("escolhe preset padrão conforme poll interval", () => {
    expect(resolveDefaultHistoryPreset(200)).toBe("1m");
    expect(resolveDefaultHistoryPreset(5000)).toBe("15m");
    expect(resolveDefaultHistoryPreset(30_000)).toBe("1h");
    expect(resolveDefaultHistoryPreset(120_000)).toBe("24h");
  });

  it("monta bounds relativos ao agora", () => {
    const now = Date.parse("2026-09-02T14:00:00.000Z");
    const bounds = boundsForHistoryPreset("1h", now);
    expect(bounds.toIso).toBe("2026-09-02T14:00:00.000Z");
    expect(bounds.fromIso).toBe("2026-09-02T13:00:00.000Z");
  });

  it("monta bounds de este mês e últimos 12 meses", () => {
    const now = Date.parse("2026-09-15T18:30:00.000Z");
    const month = boundsForHistoryPreset("month", now);
    expect(month.toIso).toBe("2026-09-15T18:30:00.000Z");
    const monthFrom = new Date(month.fromIso);
    expect(monthFrom.getDate()).toBe(1);
    expect(monthFrom.getMonth()).toBe(new Date(now).getMonth());
    expect(monthFrom.getFullYear()).toBe(2026);
    expect(monthFrom.getHours()).toBe(0);
    expect(monthFrom.getMinutes()).toBe(0);

    const twelve = boundsForHistoryPreset("12m", now);
    expect(twelve.toIso).toBe("2026-09-15T18:30:00.000Z");
    const twelveFrom = new Date(twelve.fromIso);
    expect(twelveFrom.getFullYear()).toBe(2025);
    expect(twelveFrom.getMonth()).toBe(8);
    expect(twelveFrom.getDate()).toBe(15);

    const thirty = boundsForHistoryPreset("30d", now);
    expect(Date.parse(thirty.toIso) - Date.parse(thirty.fromIso)).toBe(30 * 24 * 60 * 60_000);
  });

  it("converte datetime-local local ↔ ISO", () => {
    const local = toDatetimeLocalValue(new Date("2026-09-02T15:30:00"));
    expect(local).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
    const iso = datetimeLocalToIso(local);
    expect(iso).toBeTruthy();
    expect(Number.isNaN(Date.parse(iso!))).toBe(false);
  });

  it("adapta granularidade do eixo ao intervalo, independente do poll rápido", () => {
    expect(
      resolveChartTickGranularity(
        "2026-09-02T14:00:00.000Z",
        "2026-09-02T14:02:00.000Z",
        200,
      ),
    ).toBe("second");
    expect(
      resolveChartTickGranularity(
        "2026-09-02T10:00:00.000Z",
        "2026-09-02T14:00:00.000Z",
        200,
      ),
    ).toBe("minute");
    expect(
      resolveChartTickGranularity(
        "2026-09-01T14:00:00.000Z",
        "2026-09-02T14:00:00.000Z",
        200,
      ),
    ).toBe("hour");
    expect(
      resolveChartTickGranularity(
        "2026-08-26T14:00:00.000Z",
        "2026-09-02T14:00:00.000Z",
        200,
      ),
    ).toBe("hour");
    expect(
      resolveChartTickGranularity(
        "2026-08-01T14:00:00.000Z",
        "2026-09-02T14:00:00.000Z",
        200,
      ),
    ).toBe("day");
  });

  it("formata ticks conforme granularidade", () => {
    const iso = "2026-09-02T14:05:09.000Z";
    expect(formatChartTick(iso, "second")).toMatch(/\d{2}:\d{2}:\d{2}/);
    expect(formatChartTick(iso, "minute")).toMatch(/\d{2}:\d{2}/);
    expect(formatChartTick(iso, "day")).toMatch(/\d{2}\/\d{2}/);
  });

  it("limita page size do gráfico e faz downsample", () => {
    expect(
      resolveHistoryChartPageSize(
        "2026-09-02T14:00:00.000Z",
        "2026-09-02T14:01:00.000Z",
        200,
      ),
    ).toBe(304);
    expect(resolveHistoryChartPageSize("2026-09-01T14:00:00.000Z", "2026-09-02T14:00:00.000Z", 200)).toBe(
      500,
    );

    const points = Array.from({ length: 200 }, (_, index) => ({
      x: `2026-09-02T14:00:${String(index % 60).padStart(2, "0")}.000Z`,
      y: index,
      label: String(index),
    }));
    const reduced = downsampleChartPoints(points, 20);
    expect(reduced.length).toBeLessThanOrEqual(20);
    expect(reduced[0]?.y).toBe(0);
    expect(reduced[reduced.length - 1]?.y).toBe(199);

    const labeled = applyAdaptiveChartLabels(reduced.slice(0, 2), "minute");
    expect(labeled[0]?.label).toMatch(/\d{2}:\d{2}/);
  });

  it("pede sampleIntervalMs só quando o período excede o pageSize do gráfico", () => {
    expect(
      resolveHistoryChartSampleIntervalMs(
        "2026-09-02T14:00:00.000Z",
        "2026-09-02T14:01:00.000Z",
        200,
      ),
    ).toBeUndefined();

    const sample = resolveHistoryChartSampleIntervalMs(
      "2026-08-26T14:00:00.000Z",
      "2026-09-02T14:00:00.000Z",
      200,
    );
    expect(sample).toBeGreaterThan(200);
    expect(sample).toBeGreaterThanOrEqual(Math.ceil((7 * 24 * 60 * 60_000) / 96));

    const longCustom = resolveHistoryChartSampleIntervalMs(
      "2026-05-26T20:40:00.000Z",
      "2026-09-02T20:40:00.000Z",
      200,
    );
    expect(longCustom).toBeDefined();
    expect(longCustom!).toBeLessThanOrEqual(HISTORY_CHART_SAMPLE_INTERVAL_MS_MAX);
    expect(longCustom!).toBeGreaterThan(86_400_000);
  });
});
