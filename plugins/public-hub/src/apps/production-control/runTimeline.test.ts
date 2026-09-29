import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { RunTimelineItem } from "./api.ts";
import {
  elapsedSeconds,
  formatDurationHms,
  liveDurationSeconds,
  liveSummary,
  serverClockOffsetMs,
  serverNowMs,
  stateLabel,
} from "./runTimeline.ts";

const item: RunTimelineItem = {
  id: "ev-1",
  state: "stopped",
  startedAt: "2026-09-28T14:00:00Z",
  endedAt: null,
  durationSeconds: 300,
  source: "operator",
  downtime: null,
};

describe("server clock offset", () => {
  it("computes the drift between local clock and referenceAt", () => {
    const local = Date.parse("2026-09-28T15:00:00Z");
    const offset = serverClockOffsetMs("2026-09-28T15:00:10Z", local);
    assert.equal(offset, 10_000);
    assert.equal(serverNowMs(local + 5_000, offset), Date.parse("2026-09-28T15:00:15Z"));
  });

  it("returns zero for invalid referenceAt", () => {
    assert.equal(serverClockOffsetMs("não-é-data", 1000), 0);
  });
});

describe("elapsedSeconds", () => {
  it("derives from startedAt, not an incrementing counter", () => {
    const now = Date.parse("2026-09-28T14:04:37Z");
    assert.equal(elapsedSeconds("2026-09-28T14:00:00Z", now), 277);
  });

  it("never returns negative", () => {
    assert.equal(elapsedSeconds("2026-09-28T15:00:00Z", Date.parse("2026-09-28T14:00:00Z")), 0);
  });

  it("corrects time jumps (rerender never restarts the timer)", () => {
    const t0 = Date.parse("2026-09-28T14:00:00Z");
    const t1 = t0 + 10 * 60_000; // aba ficou 10min em background
    assert.equal(elapsedSeconds("2026-09-28T14:00:00Z", t1), 600);
  });
});

describe("formatDurationHms", () => {
  it("formats HH:MM:SS and does not cap at 59 minutes", () => {
    assert.equal(formatDurationHms(8), "00:00:08");
    assert.equal(formatDurationHms(277), "00:04:37");
    assert.equal(formatDurationHms(4930), "01:22:10");
    assert.equal(formatDurationHms(360000), "100:00:00");
    assert.equal(formatDurationHms(-5), "00:00:00");
  });
});

describe("liveDurationSeconds", () => {
  it("open segment grows with server clock", () => {
    const now = Date.parse("2026-09-28T14:10:00Z");
    assert.equal(liveDurationSeconds(item, now), 600);
  });

  it("closed segment keeps stored duration", () => {
    const closed = { ...item, endedAt: "2026-09-28T14:05:00Z", durationSeconds: 300 };
    assert.equal(liveDurationSeconds(closed, Date.parse("2030-01-01T00:00:00Z")), 300);
  });
});

describe("stateLabel", () => {
  it("maps all MES operational states", () => {
    assert.equal(stateLabel("producing"), "Produzindo");
    assert.equal(stateLabel("stopped"), "Parado");
    assert.equal(stateLabel("setup"), "Preparação");
    assert.equal(stateLabel("idle"), "Livre");
    assert.equal(stateLabel("planned_stop"), "Parada planejada");
    assert.equal(stateLabel("custom_x"), "custom_x");
  });
});

describe("liveSummary", () => {
  const closed = (
    state: string,
    durationSeconds: number,
  ): RunTimelineItem => ({
    id: `${state}-${durationSeconds}`,
    state,
    startedAt: "2026-09-28T14:00:00Z",
    endedAt: "2026-09-28T14:05:00Z",
    durationSeconds,
    source: "state",
    downtime: null,
  });

  it("open stopped keeps accumulating without a new GET", () => {
    const open: RunTimelineItem = {
      id: "s-open",
      state: "stopped",
      startedAt: "2026-09-28T14:10:00Z",
      endedAt: null,
      durationSeconds: 0,
      source: "state",
      downtime: null,
    };
    const items = [closed("producing", 300), open];
    const t1 = liveSummary(items, Date.parse("2026-09-28T14:11:00Z"));
    assert.equal(t1.producingSeconds, 300);
    assert.equal(t1.stoppedSeconds, 60);
    assert.equal(t1.stopCount, 1);
    const t2 = liveSummary(items, Date.parse("2026-09-28T14:16:00Z"));
    assert.equal(t2.stoppedSeconds, 360);
    assert.equal(t2.producingSeconds, 300);
  });
});
