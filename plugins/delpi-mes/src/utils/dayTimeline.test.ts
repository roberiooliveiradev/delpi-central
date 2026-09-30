import { describe, expect, it } from "vitest";
import type { WorkCenterTimelineItem } from "../types/mes";
import {
  buildDaySegments, dayEventContext, dayEventDurationSeconds, dayEventReason,
  dayRangeIso, downtimeReasonTotals, formatDayEventRange, formatHoursMinutes,
  localDayKey, presentDayEvent, startOfLocalDayIso, summarizeDay,
} from "./dayTimeline";

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

  it("shows the operator note when the downtime reason is Outro", () => {
    const other = item({ state: "stopped", downtime: { id: "d", source: "operator", reasonCode: "other", reasonLabel: "Outro", category: null, confirmed: true, note: "Troca de ferramental emergencial" } });
    expect(dayEventReason(other, presentDayEvent(other))).toBe("Outro (Troca de ferramental emergencial)");
    const otherCode = item({ state: "stopped", downtime: { id: "d", source: "operator", reasonCode: "outro", reasonLabel: "Outro", category: null, confirmed: true, note: "Vazamento hidráulico" } });
    expect(dayEventReason(otherCode, presentDayEvent(otherCode))).toBe("Outro (Vazamento hidráulico)");
    const withoutNote = item({ state: "stopped", downtime: { id: "d", source: "operator", reasonCode: "outro", reasonLabel: "Outro", category: null, confirmed: true, note: null } });
    expect(dayEventReason(withoutNote, presentDayEvent(withoutNote))).toBe("Outro");
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

  it("builds day segments with inactivity gaps covering the whole day", () => {
    const segments = buildDaySegments([
      item({ startedAt: "2026-01-01T08:02:00.000Z", endedAt: "2026-01-01T08:47:00.000Z" }),
      item({ state: "stopped", startedAt: "2026-01-01T08:47:00.000Z", endedAt: "2026-01-01T08:56:00.000Z" }),
    ], FROM, NOW);
    expect(segments.map((segment) => segment.state)).toEqual(["inactive", "producing", "stopped", "inactive"]);
    expect(segments[0].endMs).toBe(Date.parse("2026-01-01T08:02:00.000Z"));
    expect(segments[2].startMs).toBe(Date.parse("2026-01-01T08:47:00.000Z"));
  });

  it("ends an open event at now and fills the rest of the day as inactive", () => {
    const segments = buildDaySegments([item({ startedAt: "2026-01-01T11:00:00.000Z", endedAt: null })], FROM, NOW);
    const open = segments.find((segment) => segment.state === "producing");
    expect(open?.endMs).toBe(NOW);
    expect(segments[segments.length - 1].state).toBe("inactive");
  });

  it("summarizes producing time, stopped time, stops and availability", () => {
    const segments = buildDaySegments([
      item({ startedAt: "2026-01-01T00:00:00.000Z", endedAt: "2026-01-01T09:00:00.000Z" }),
      item({ state: "stopped", startedAt: "2026-01-01T09:00:00.000Z", endedAt: "2026-01-01T10:00:00.000Z" }),
      item({ state: "stopped", startedAt: "2026-01-01T10:00:00.000Z", endedAt: "2026-01-01T11:00:00.000Z" }),
    ], FROM, NOW);
    const summary = summarizeDay(segments, FROM, NOW);
    expect(summary.producingSec).toBe(9 * 3600);
    expect(summary.stoppedSec).toBe(2 * 3600);
    expect(summary.stops).toBe(2);
    expect(summary.availabilityPct).toBe(75);
  });

  it("aggregates downtime reasons ordered by total duration", () => {
    const stopsItems = [
      item({ state: "stopped", startedAt: "2026-01-01T08:00:00.000Z", endedAt: "2026-01-01T08:30:00.000Z", downtime: { id: "1", source: "o", reasonCode: "m", reasonLabel: "Falta de material", category: null, confirmed: true, note: null } }),
      item({ state: "stopped", startedAt: "2026-01-01T09:00:00.000Z", endedAt: "2026-01-01T09:10:00.000Z", downtime: { id: "2", source: "o", reasonCode: "s", reasonLabel: "Setup", category: null, confirmed: true, note: null } }),
      item({ state: "stopped", startedAt: "2026-01-01T09:10:00.000Z", endedAt: "2026-01-01T09:20:00.000Z", downtime: { id: "3", source: "o", reasonCode: null, reasonLabel: null, category: null, confirmed: false, note: null } }),
    ];
    const totals = downtimeReasonTotals(buildDaySegments(stopsItems, FROM, NOW));
    expect(totals.map((t) => t.label)).toEqual(["Falta de material", "Setup", "Sem motivo informado"]);
    expect(totals[0].seconds).toBe(1800);
  });

  it("formats hours and minutes and resolves day ranges", () => {
    expect(formatHoursMinutes(9 * 3600 + 42 * 60)).toBe("9h 42min");
    expect(formatHoursMinutes(14 * 60)).toBe("0h 14min");
    const today = dayRangeIso(localDayKey(), new Date());
    expect(today.to).toBeUndefined();
    expect(new Date(today.from).getHours()).toBe(0);
    const past = dayRangeIso("2020-05-10", new Date());
    expect(past.to).toBeDefined();
    expect(new Date(past.from).getHours()).toBe(0);
  });
});
