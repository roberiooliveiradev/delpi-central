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
});
