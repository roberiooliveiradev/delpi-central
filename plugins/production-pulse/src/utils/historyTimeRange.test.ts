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

  it("converte datetime-local local ↔ ISO", () => {
    const local = toDatetimeLocalValue(new Date("2026-09-02T15:30:00"));
    expect(local).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
    const iso = datetimeLocalToIso(local);
    expect(iso).toBeTruthy();
    expect(Number.isNaN(Date.parse(iso!))).toBe(false);
  });

  it("adapta granularidade do eixo ao intervalo", () => {
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
        5000,
      ),
    ).toBe("minute");
    expect(
      resolveChartTickGranularity(
        "2026-08-28T14:00:00.000Z",
        "2026-09-02T14:00:00.000Z",
        60_000,
      ),
    ).toBe("hour");
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
});
