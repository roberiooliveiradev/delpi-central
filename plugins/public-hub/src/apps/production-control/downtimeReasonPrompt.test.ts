import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  isDowntimeReasonInformed,
  resolveDowntimeReasonPrompt,
} from "./downtimeReasonPrompt.ts";

const open = {
  id: "dt-open",
  confirmed: false,
  reasonCode: null,
  reasonLabel: null,
  endedAt: null,
};

const pending = {
  id: "dt-old",
  confirmed: false,
  reasonCode: null,
  reasonLabel: null,
  endedAt: "2026-01-01T10:30:00Z",
};

describe("resolveDowntimeReasonPrompt", () => {
  it("pede o motivo da parada em registro ainda sem classificação", () => {
    assert.equal(resolveDowntimeReasonPrompt(open, pending)?.id, "dt-open");
  });

  it("não pede de novo quando a parada em registro já foi confirmada", () => {
    const informed = { ...open, confirmed: true, reasonCode: "break", reasonLabel: "Intervalo" };
    assert.equal(resolveDowntimeReasonPrompt(informed, pending), null);
  });

  it("não pede de novo quando o motivo já está no snapshot mesmo sem o flag", () => {
    const labeled = { ...open, confirmed: false, reasonLabel: "Intervalo" };
    assert.equal(isDowntimeReasonInformed(labeled), true);
    assert.equal(resolveDowntimeReasonPrompt(labeled, pending), null);
  });

  it("pede a pendência encerrada quando não há parada em registro", () => {
    assert.equal(resolveDowntimeReasonPrompt(null, pending)?.id, "dt-old");
  });

  it("não pede pendência que já tem motivo", () => {
    const informedPending = { ...pending, confirmed: true, reasonCode: "setup" };
    assert.equal(resolveDowntimeReasonPrompt(null, informedPending), null);
    assert.equal(resolveDowntimeReasonPrompt(null, null), null);
  });
});
