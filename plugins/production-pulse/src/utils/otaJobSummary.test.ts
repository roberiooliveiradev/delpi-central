import { describe, expect, it } from "vitest";

import type { FirmwareUpdateTarget } from "../api/productionPulseApi";
import { jobStatusToOtaPhase, summarizeOtaJobTargets } from "./otaJobSummary";

function target(partial: Partial<FirmwareUpdateTarget>): FirmwareUpdateTarget {
  return {
    id: partial.id || "t1",
    jobId: "j1",
    deviceId: "d1",
    status: partial.status || "authorized",
    fromVersion: null,
    toVersion: "1.0.0",
    errorCode: null,
    ...partial,
  };
}

describe("summarizeOtaJobTargets", () => {
  it("aggregates phases and processed percent", () => {
    const summary = summarizeOtaJobTargets([
      target({ id: "a", status: "updated" }),
      target({ id: "b", status: "updated" }),
      target({ id: "c", status: "downloading", progressPercent: 40 }),
      target({ id: "d", status: "authorized" }),
      target({ id: "e", status: "failed", errorCode: "ota_target_stale" }),
    ]);
    expect(summary.total).toBe(5);
    expect(summary.updated).toBe(2);
    expect(summary.downloading).toBe(1);
    expect(summary.awaiting).toBe(1);
    expect(summary.failed).toBe(1);
    expect(summary.terminal).toBe(3);
    expect(summary.processedPercent).toBe(60);
    expect(summary.phaseStatus).toBe("downloading");
  });

  it("marks all-failed as failed phase", () => {
    const summary = summarizeOtaJobTargets([
      target({ id: "a", status: "failed" }),
      target({ id: "b", status: "failed" }),
    ]);
    expect(summary.phaseStatus).toBe("failed");
    expect(summary.processedPercent).toBe(100);
  });
});

describe("jobStatusToOtaPhase", () => {
  it("maps job lifecycle to visual phases", () => {
    expect(jobStatusToOtaPhase("running")).toBe("applying");
    expect(jobStatusToOtaPhase("completed")).toBe("updated");
    expect(jobStatusToOtaPhase("scheduled")).toBe("pending");
    expect(jobStatusToOtaPhase("cancelled")).toBe("cancelled");
  });
});
