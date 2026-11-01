import { describe, expect, it, vi } from "vitest";

const httpGetMock = vi.fn();
vi.mock("./httpClient", () => ({
  cfApiUrl: (path: string) => `http://bff${path}`,
  httpGet: (...args: unknown[]) => httpGetMock(...args),
}));

import { getCostClosingState } from "./costClosingStateApi";

const payload = {
  report: "cost-closing-state",
  period: "2026-09",
  referenceDate: "2026-09-30",
  officiality: "technical_markers",
  observedAt: "2026-10-31T20:00:00Z",
  branches: {
    "01": {
      snapshot: { state: "available", evidenceRefs: {}, limitations: [] },
      cutoff_marker: { state: "observed", evidenceRefs: {}, limitations: [] },
      cost_evidence: { state: "observed", evidenceRefs: {}, limitations: [] },
      wizard_lifecycle: { state: "unavailable", evidenceRefs: {}, limitations: [] },
      human_acceptance: { state: "not_informed", evidenceRefs: {}, limitations: [] },
    },
    "02": {
      snapshot: { state: "available", evidenceRefs: {}, limitations: [] },
      cutoff_marker: { state: "observed", evidenceRefs: {}, limitations: [] },
      cost_evidence: { state: "observed", evidenceRefs: {}, limitations: [] },
      wizard_lifecycle: { state: "unavailable", evidenceRefs: {}, limitations: [] },
      human_acceptance: { state: "not_informed", evidenceRefs: {}, limitations: [] },
    },
  },
  limitations: [],
};

describe("getCostClosingState — envelope unwrap", () => {
  it("retorna o payload interno do envelope {success,data,meta}", async () => {
    httpGetMock.mockResolvedValueOnce({
      success: true,
      message: "ok",
      data: payload,
      meta: {},
    });
    const out = await getCostClosingState("2026-09");
    expect(out.branches["01"].snapshot.state).toBe("available");
    expect(out.branches["02"].snapshot.rowCount ?? out.branches["02"].snapshot.state).toBeTruthy();
    expect(out.officiality).toBe("technical_markers");
    // regressão G034: antes do fix, o envelope era usado como payload e
    // `branches` vinha undefined → empty state indevido na página.
    expect(out.branches).not.toBeUndefined();
    expect(Object.keys(out.branches)).toHaveLength(2);
  });
});
