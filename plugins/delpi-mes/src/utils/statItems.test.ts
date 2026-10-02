import { describe, expect, it } from "vitest";
import type { MonitoringSummary } from "../types/mes";
import { monitoringDowntimeCount, monitoringStatItems } from "./statItems";

const summary = (changes: Partial<MonitoringSummary> = {}): MonitoringSummary => ({
  activeRuns: 3,
  producing: 1,
  stopped: 2,
  paused: 1,
  unclassifiedDowntimes: 1,
  ...changes,
});

describe("monitoring stat cards", () => {
  it("shows appointments, producing, a single downtime card and pending reasons", () => {
    const labels = monitoringStatItems(summary()).map((item) => item.label);
    expect(labels).toEqual([
      "Apontamentos ativos",
      "Produzindo",
      "Paradas",
      "Motivos pendentes",
    ]);
  });

  it("counts a stop once when it is also a manual pause", () => {
    const cards = monitoringStatItems(summary());
    expect(monitoringDowntimeCount(summary())).toBe(2);
    expect(cards.find((item) => item.id === "downtime")?.value).toBe(2);
    expect(cards.find((item) => item.id === "active")?.value).toBe(3);
  });

  it("counts an automatic stop that is not a manual pause", () => {
    expect(monitoringDowntimeCount(summary({ stopped: 1, paused: 0 }))).toBe(1);
  });

  it("does not count a producing appointment as a downtime", () => {
    expect(monitoringDowntimeCount(summary({ activeRuns: 1, producing: 1, stopped: 0, paused: 0 }))).toBe(0);
  });
});
