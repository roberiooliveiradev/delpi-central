import { describe, expect, it } from "vitest";

import type { DowntimeItem } from "../types/mes";
import type { DowntimesRouteParams } from "../hooks/useDelpiMesRoute";
import {
  DOWNTIME_PERIOD_PRESETS,
  buildDowntimesQuery,
  downtimeDurationSeconds,
  downtimeSourceLabel,
  downtimeStatusLabel,
  hasActiveDowntimeFilters,
  resolveDowntimePeriod,
} from "./downtimesPresentation";

const NOW = new Date("2026-02-10T12:00:00.000Z");

const localMidnight = (date: Date) => {
  const start = new Date(date);
  start.setHours(0, 0, 0, 0);
  return start;
};

const DAY_MS = 24 * 60 * 60 * 1000;

const params = (overrides: Partial<DowntimesRouteParams> = {}): DowntimesRouteParams => ({
  period: "7d",
  from: null,
  to: null,
  workCenter: null,
  reasonCode: null,
  source: null,
  classification: null,
  sort: "recent",
  downtimeId: null,
  page: 1,
  pageSize: 50,
  ...overrides,
});

const item = (overrides: Partial<DowntimeItem> = {}): DowntimeItem => ({
  id: "1",
  runId: null,
  workCenter: "CT-35",
  productionOrder: null,
  operationCode: null,
  startedAt: "2026-02-10T10:00:00.000Z",
  endedAt: null,
  source: "system",
  reasonCode: null,
  reasonLabel: null,
  category: null,
  confirmed: false,
  note: null,
  ...overrides,
});

describe("downtimesPresentation", () => {
  it("offers the four canonical period presets with 7d as the default", () => {
    expect(DOWNTIME_PERIOD_PRESETS.map((preset) => preset.id)).toEqual([
      "today",
      "7d",
      "30d",
      "custom",
    ]);
    expect(params().period).toBe("7d");
  });

  it("resolves presets against local business days", () => {
    const midnight = localMidnight(NOW);
    expect(resolveDowntimePeriod(params({ period: "today" }), NOW)).toEqual({
      from: midnight.toISOString(),
    });
    expect(resolveDowntimePeriod(params({ period: "7d" }), NOW)).toEqual({
      from: new Date(midnight.getTime() - 6 * DAY_MS).toISOString(),
    });
    expect(resolveDowntimePeriod(params({ period: "30d" }), NOW)).toEqual({
      from: new Date(midnight.getTime() - 29 * DAY_MS).toISOString(),
    });
  });

  it("converts custom day keys into a half-open interval covering the end day", () => {
    const window = resolveDowntimePeriod(
      params({ period: "custom", from: "2026-02-01", to: "2026-02-10" }),
      NOW,
    );
    expect(window.from).toBe(localMidnight(new Date(2026, 1, 1)).toISOString());
    expect(window.to).toBe(localMidnight(new Date(2026, 1, 11)).toISOString());
  });

  it("emits only the bounds actually selected in custom mode", () => {
    const openEnd = resolveDowntimePeriod(params({ period: "custom", from: "2026-02-01" }), NOW);
    expect(openEnd.to).toBeUndefined();
    const openStart = resolveDowntimePeriod(params({ period: "custom", to: "2026-02-10" }), NOW);
    expect(openStart.from).toBeUndefined();
  });

  it("builds the API query without ever forwarding the selected downtime id", () => {
    const query = buildDowntimesQuery(
      "01",
      params({
        workCenter: " CT-35 ",
        reasonCode: "SETUP",
        source: "system",
        classification: "pending",
        sort: "oldest",
        downtimeId: "42",
        page: 3,
        pageSize: 100,
      }),
      NOW,
    );
    expect(query.branch).toBe("01");
    expect(query.workCenter).toBe("CT-35");
    expect(query.reasonCode).toBe("SETUP");
    expect(query.source).toBe("system");
    expect(query.classification).toBe("pending");
    expect(query.sort).toBe("oldest");
    expect(query.page).toBe(3);
    expect(query.pageSize).toBe(100);
    expect(query.from).toBe(new Date(localMidnight(NOW).getTime() - 6 * DAY_MS).toISOString());
    expect(query.downtimeId).toBeUndefined();
  });

  it("clamps a non-positive page back to the first page", () => {
    expect(buildDowntimesQuery("01", params({ page: 0 }), NOW).page).toBe(1);
  });

  it("flags only real filters as active", () => {
    expect(hasActiveDowntimeFilters(params())).toBe(false);
    expect(hasActiveDowntimeFilters(params({ workCenter: "CT-35" }))).toBe(true);
    expect(hasActiveDowntimeFilters(params({ sort: "oldest" }))).toBe(true);
    expect(hasActiveDowntimeFilters(params({ period: "today" }))).toBe(true);
    expect(hasActiveDowntimeFilters(params({ downtimeId: "9" }))).toBe(false);
  });

  it("computes closed duration from endedAt and open duration from the server clock", () => {
    const closed = item({ endedAt: "2026-02-10T11:30:00.000Z" });
    expect(downtimeDurationSeconds(closed, Date.parse("2026-02-10T12:00:00.000Z"))).toBe(5400);
    const open = item();
    expect(downtimeDurationSeconds(open, Date.parse("2026-02-10T12:00:00.000Z"))).toBe(7200);
  });

  it("never reports a real zero duration for invalid or missing dates", () => {
    expect(downtimeDurationSeconds(item({ startedAt: "not-a-date" }), Date.now())).toBeNull();
    expect(downtimeDurationSeconds(item({ startedAt: null }), Date.now())).toBeNull();
    expect(
      downtimeDurationSeconds(
        item({ endedAt: "invalid" }),
        Date.parse("2026-02-10T12:00:00.000Z"),
      ),
    ).toBeNull();
  });

  it("distinguishes open/closed and pending/confirmed as independent states", () => {
    const openPending = downtimeStatusLabel(item());
    expect(openPending.state).toBe("Aberta");
    expect(openPending.classification).toBe("Pendente");
    const closedConfirmed = downtimeStatusLabel(
      item({ endedAt: "2026-02-10T11:00:00.000Z", confirmed: true }),
    );
    expect(closedConfirmed.state).toBe("Encerrada");
    expect(closedConfirmed.classification).toBe("Confirmada");
    const closedPending = downtimeStatusLabel(
      item({ endedAt: "2026-02-10T11:00:00.000Z", confirmed: false }),
    );
    expect(closedPending.state).toBe("Encerrada");
    expect(closedPending.classification).toBe("Pendente");
  });

  it("labels canonical sources and preserves unknown domain values", () => {
    expect(downtimeSourceLabel("operator_pause")).toBe("Pausa do operador");
    expect(downtimeSourceLabel("automatic_detection")).toBe("Detecção automática");
    expect(downtimeSourceLabel("system")).toBe("Sistema");
    expect(downtimeSourceLabel("recovery")).toBe("Recuperação");
    expect(downtimeSourceLabel("integration")).toBe("Integração");
    expect(downtimeSourceLabel("some_new_source")).toBe("some_new_source");
    expect(downtimeSourceLabel(null)).toBe("Não informado");
  });
});
