import attachmentsContent from "./attachments_content.json";

const PROGRESS = attachmentsContent.ingestUi.progress;

export type IngestProgressInput = {
  percent?: number | null;
  done?: number;
  total?: number;
};

/** Percentual 0–100 ou `null` quando indeterminado. */
export function resolveIngestProgressPercent(input: IngestProgressInput): number | null {
  if (typeof input.percent === "number" && Number.isFinite(input.percent)) {
    return Math.max(0, Math.min(100, Math.round(input.percent)));
  }

  const total = input.total;
  const done = input.done;
  if (typeof total === "number" && total > 0 && typeof done === "number" && Number.isFinite(done)) {
    return Math.max(0, Math.min(100, Math.round((done / total) * 100)));
  }

  return null;
}

export function ingestProgressPercentLabel(percent: number): string {
  return PROGRESS.percentLabel.replace("{percent}", String(percent));
}

export function ingestProgressFractionLabel(done: number, total: number): string {
  return PROGRESS.fractionLabel
    .replace("{done}", String(done))
    .replace("{total}", String(total));
}

export function ingestProgressIndeterminateLabel(): string {
  return PROGRESS.indeterminateLabel;
}
