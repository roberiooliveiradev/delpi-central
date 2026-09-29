import { describe, expect, it } from "vitest";
import type { WorkCenterTimelineItem } from "../types/mes";
import { dayEventContext, dayEventDurationSeconds, dayEventReason, formatDayEventRange, presentDayEvent, startOfLocalDayIso } from "./dayTimeline";

const FROM = "2026-01-01T00:00:00.000Z";
const TO = "2026-01-01T12:00:00.000Z";
const NOW = Date.parse(TO);

const item = (changes: Partial<WorkCenterTimelineItem> = {}): WorkCenterTimelineItem => ({
  stateEventId: "e1", runId: "run-1", productionOrder: "123456", operationCode: "20",
  state: "producing", startedAt: "2026-01-01T08:02:00.000Z", endedAt: "2026-01-01T08:47:00.000Z",
  source: "operator", downtime: null, ...changes,
});

describe("work center day timeline", () => {
  it("maps known states without inventing domains", () => {
    expect(presentDayEvent(item()).label).toBe("Produzindo");
    expect(presentDayEvent(item({ state: "stopped" })).label).toBe("Parada");
    expect(presentDayEvent(item({ state: "setup" })).label).toBe("Setup");
    expect(presentDayEvent(item({ state: "planned_stop" })).label).toBe("Parada planejada");
    expect(presentDayEvent(item({ state: "idle" })).label).toBe("Livre");
    expect(presentDayEvent(item({ state: "unknown" })).label).toBe("Estado indisponível");
  });

  it("marks pending downtime reasons", () => {
    const pending = item({ state: "stopped", downtime: { id: "d", source: "system", reasonCode: null, reasonLabel: null, category: null, confirmed: false, note: null } });
    expect(presentDayEvent(pending).pendingReason).toBe(true);
    expect(dayEventReason(pending, presentDayEvent(pending))).toBe("Motivo pendente");
    const confirmed = item({ state: "stopped", downtime: { id: "d", source: "operator", reasonCode: "raw_material", reasonLabel: "Falta de material", category: "material", confirmed: true, note: null } });
    expect(dayEventReason(confirmed, presentDayEvent(confirmed))).toBe("Falta de material");
    expect(dayEventReason(item(), presentDayEvent(item()))).toBeNull();
  });

  it("clips durations to the requested window", () => {
    const crossing = item({ startedAt: "2025-12-31T23:58:00.000Z", endedAt: "2026-01-01T00:10:00.000Z" });
    expect(dayEventDurationSeconds(crossing, FROM, TO, NOW)).toBe(600);
    const afterTo = item({ startedAt: "2026-01-01T11:00:00.000Z", endedAt: "2026-01-01T13:00:00.000Z" });
    expect(dayEventDurationSeconds(afterTo, FROM, TO, NOW)).toBe(3600);
    expect(dayEventDurationSeconds(item(), FROM, TO, NOW)).toBe(2700);
  });

  it("shows an open event as agora and evolves its duration with server now", () => {
    const open = item({ startedAt: "2026-01-01T11:05:00.000Z", endedAt: null });
    expect(formatDayEventRange(open, FROM, TO, NOW)).toContain("agora");
    expect(dayEventDurationSeconds(open, FROM, TO, NOW)).toBe(3300);
    expect(dayEventDurationSeconds(open, FROM, TO, NOW + 10_000)).toBe(3310);
  });

  it("keeps run context visible for OP changes", () => {
    expect(dayEventContext(item())).toBe("OP 123456 · Operação 20");
    expect(dayEventContext(item({ productionOrder: null, operationCode: null }))).toBe("");
  });

  it("computes the local start of day as an ISO instant", () => {
    const from = startOfLocalDayIso(new Date("2026-01-01T15:30:00"));
    expect(Date.parse(from)).toBeLessThanOrEqual(Date.parse("2026-01-01T15:30:00"));
    expect(new Date(from).getHours()).toBe(0);
  });
});
