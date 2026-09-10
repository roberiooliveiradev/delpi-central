import type { FirmwareUpdateTarget } from "../api/productionPulseApi";

export type OtaJobTargetsSummary = {
  total: number;
  terminal: number;
  updated: number;
  downloading: number;
  awaiting: number;
  applying: number;
  failed: number;
  /** Aggregate progress: terminal / total (lifecycle), not download %. */
  processedPercent: number;
  /** Representative phase for OtaStatusIndicator. */
  phaseStatus: string;
};

export function summarizeOtaJobTargets(
  targets: FirmwareUpdateTarget[],
): OtaJobTargetsSummary {
  const total = targets.length;
  const updated = targets.filter((t) => (t.status || "").toLowerCase() === "updated").length;
  const downloading = targets.filter(
    (t) => (t.status || "").toLowerCase() === "downloading",
  ).length;
  const awaiting = targets.filter((t) =>
    ["pending", "authorized"].includes((t.status || "").toLowerCase()),
  ).length;
  const applying = targets.filter((t) => (t.status || "").toLowerCase() === "applying").length;
  const failed = targets.filter((t) => (t.status || "").toLowerCase() === "failed").length;
  const terminal = targets.filter((t) =>
    ["updated", "failed", "cancelled", "skipped"].includes((t.status || "").toLowerCase()),
  ).length;
  const processedPercent = total > 0 ? Math.round((terminal / total) * 100) : 0;

  let phaseStatus = "applying";
  if (total === 0) phaseStatus = "authorized";
  else if (failed > 0 && terminal === total) phaseStatus = "failed";
  else if (terminal === total && updated === total) phaseStatus = "updated";
  else if (terminal === total && failed > 0) phaseStatus = "failed";
  else if (downloading > 0) phaseStatus = "downloading";
  else if (applying > 0) phaseStatus = "applying";
  else if (awaiting > 0) phaseStatus = "authorized";
  else if (terminal === total) phaseStatus = updated > 0 ? "updated" : "failed";

  return {
    total,
    terminal,
    updated,
    downloading,
    awaiting,
    applying,
    failed,
    processedPercent,
    phaseStatus,
  };
}

/** Map job lifecycle status when target list is unavailable. */
export function jobStatusToOtaPhase(jobStatus: string | null | undefined): string {
  const s = (jobStatus || "").toLowerCase();
  switch (s) {
    case "scheduled":
    case "draft":
    case "pending":
      return "pending";
    case "running":
      return "applying";
    case "completed":
      return "updated";
    case "failed":
      return "failed";
    case "cancelled":
      return "cancelled";
    default:
      return s || "authorized";
  }
}
