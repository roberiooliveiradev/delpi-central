import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { MesWorkCenterTodayItem } from "./api.ts";
import {
  classifiableDowntime,
  formatTimeHmSp,
  isReasonPending,
  spCivilDayKey,
  timelineSegments,
} from "./workCenterActivity.ts";

const item = (over: Partial<MesWorkCenterTodayItem>): MesWorkCenterTodayItem => ({
  stateEventId: "se-1",
  runId: "r1",
  productionOrder: "OP-1",
  operationCode: "10",
  state: "stopped",
  startedAt: "2026-10-19T12:00:00Z",
  endedAt: "2026-10-19T13:00:00Z",
  source: "system",
  effectiveDurationSeconds: 3600,
  downtime: null,
  ...over,
});

describe("formatTimeHmSp", () => {
  it("renders in America/Sao_Paulo regardless of local tz", () => {
    // 13:00Z == 10:00 em SP (UTC-3).
    assert.equal(formatTimeHmSp("2026-10-19T13:00:00Z"), "10:00");
    assert.equal(formatTimeHmSp(null), "—");
    assert.equal(formatTimeHmSp("não-é-data"), "—");
  });
});

describe("spCivilDayKey", () => {
  it("reflects the civil day in Sao Paulo", () => {
    // 02:30Z do dia 20 == 23:30 do dia 19 em SP.
    const key = spCivilDayKey(new Date("2026-10-20T02:30:00Z"));
    assert.equal(key, "2026-10-19");
  });
});

describe("timelineSegments", () => {
  const from = "2026-10-19T03:00:00Z"; // 00:00 SP
  const to = "2026-10-19T16:00:00Z"; // 13:00 SP

  it("positions segments by real time and leaves gaps neutral", () => {
    const segs = timelineSegments(
      [
        item({ state: "producing", startedAt: "2026-10-19T06:00:00Z", endedAt: "2026-10-19T09:00:00Z" }),
        item({ state: "stopped", startedAt: "2026-10-19T13:00:00Z", endedAt: "2026-10-19T14:00:00Z" }),
      ],
      from,
      to,
    );
    assert.equal(segs.length, 2);
    // 13h de janela: producing das 03h às 06h da posição UTC — 3h/13h ≈ 23%.
    assert.ok(Math.abs(segs[0].leftPct - (3 / 13) * 100) < 0.01);
    assert.ok(Math.abs(segs[0].widthPct - (3 / 13) * 100) < 0.01);
    // gap 09h–13h não vira segmento.
    assert.ok(Math.abs(segs[1].leftPct - (10 / 13) * 100) < 0.01);
  });

  it("clips an overnight stop to the day window", () => {
    // começou 23h50 de ontem (02:50Z), terminou 00h20 (03:20Z)
    const segs = timelineSegments(
      [item({ startedAt: "2026-10-19T02:50:00Z", endedAt: "2026-10-19T03:20:00Z" })],
      from,
      to,
    );
    assert.equal(segs.length, 1);
    assert.equal(segs[0].leftPct, 0);
    assert.ok(Math.abs(segs[0].widthPct - (20 / (13 * 60)) * 100) < 0.01);
  });

  it("treats an open item as ending at the window edge", () => {
    const segs = timelineSegments(
      [item({ startedAt: "2026-10-19T15:00:00Z", endedAt: null })],
      from,
      to,
    );
    assert.equal(segs.length, 1);
    assert.ok(Math.abs(segs[0].leftPct + segs[0].widthPct - 100) < 0.01);
  });

  it("returns empty for invalid window", () => {
    assert.deepEqual(timelineSegments([item({})], to, from), []);
    assert.deepEqual(timelineSegments([item({})], "x", to), []);
  });
});

describe("classifiableDowntime", () => {
  it("requires the downtime id; autonomous stops (runId null) are classifiable", () => {
    assert.equal(classifiableDowntime(item({ downtime: null })), null);
    assert.deepEqual(
      classifiableDowntime(item({ runId: null, downtime: { id: "d1", reasonCode: null, reasonLabel: null, category: null, note: null, confirmed: false } })),
      { runId: null, downtimeId: "d1" },
    );
    assert.deepEqual(
      classifiableDowntime(item({ downtime: { id: "d1", reasonCode: null, reasonLabel: null, category: null, note: null, confirmed: false } })),
      { runId: "r1", downtimeId: "d1" },
    );
  });
});

describe("isReasonPending", () => {
  it("uses pendingReason from the backend, not local inference", () => {
    // reasonCode preenchido mas pendente: confirmado=false.
    assert.equal(
      isReasonPending(item({ downtime: { id: "d", reasonCode: "setup", reasonLabel: "Setup", category: null, note: null, confirmed: false, pendingReason: true } })),
      true,
    );
    // setup confirmado pelo sistema: não é pendência.
    assert.equal(
      isReasonPending(item({ downtime: { id: "d", reasonCode: "setup", reasonLabel: "Setup", category: null, note: null, confirmed: true, pendingReason: false } })),
      false,
    );
    assert.equal(isReasonPending(item({ downtime: null })), false);
  });
});
