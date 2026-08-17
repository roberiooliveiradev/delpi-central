import assert from "node:assert/strict";
import { describe, it } from "node:test";

function pad2(n) {
  return String(n).padStart(2, "0");
}

function localDateInputValue(date = new Date()) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

function dueDateInputToIsoEod(dateStr) {
  const [y, m, d] = dateStr.split("-").map((part) => Number(part));
  if (!y || !m || !d) return new Date().toISOString();
  return new Date(y, m - 1, d, 23, 59, 0, 0).toISOString();
}

describe("myDayDueDate", () => {
  it("localDateInputValue formata YYYY-MM-DD", () => {
    assert.equal(localDateInputValue(new Date(2026, 7, 6)), "2026-08-06");
  });

  it("dueDateInputToIsoEod usa fim do dia local", () => {
    const parsed = new Date(dueDateInputToIsoEod("2026-08-06"));
    assert.equal(parsed.getHours(), 23);
    assert.equal(parsed.getMinutes(), 59);
    assert.equal(parsed.getDate(), 6);
  });

  it("deferDueAtOneDay avança um dia civil", () => {
    function deferDueAtOneDay(dueAt) {
      const base = dueAt ? new Date(dueAt) : new Date();
      const next = Number.isNaN(base.getTime()) ? new Date() : base;
      next.setDate(next.getDate() + 1);
      next.setHours(23, 59, 0, 0);
      return next.toISOString();
    }
    const deferred = new Date(deferDueAtOneDay("2026-08-06T12:00:00"));
    assert.equal(deferred.getDate(), 7);
    assert.equal(deferred.getHours(), 23);
  });
});
