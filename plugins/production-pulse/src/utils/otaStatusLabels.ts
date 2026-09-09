import { PP_HELP } from "../content/helpTooltips";

const ACTIVE = new Set(["pending", "authorized", "downloading", "applying"]);

export function otaStatusLabel(status: string | null | undefined): string {
  const key = (status || "").trim().toLowerCase();
  const map = PP_HELP.ota.status as Record<string, string>;
  return map[key] ?? (status || "—");
}

export function otaOperationLabel(status: string | null | undefined): string {
  const key = (status || "").trim().toLowerCase();
  const map = PP_HELP.ota.operation as Record<string, string>;
  if (!key) return map.idle;
  return map[key] ?? map.idle;
}

export function isOtaStatusActive(status: string | null | undefined): boolean {
  return ACTIVE.has((status || "").trim().toLowerCase());
}

/** Prefer device-reported percent; otherwise map phase to a coarse %. */
export function resolveOtaProgressPercent(input: {
  status?: string | null;
  progressPercent?: number | null;
}): number {
  const status = (input.status || "").trim().toLowerCase();
  if (
    typeof input.progressPercent === "number" &&
    Number.isFinite(input.progressPercent) &&
    status === "downloading"
  ) {
    return Math.min(100, Math.max(0, Math.round(input.progressPercent)));
  }
  switch (status) {
    case "pending":
      return 0;
    case "authorized":
      return 5;
    case "downloading":
      return typeof input.progressPercent === "number"
        ? Math.min(100, Math.max(0, Math.round(input.progressPercent)))
        : 25;
    case "applying":
      return 95;
    case "updated":
      return 100;
    case "failed":
    case "cancelled":
    case "skipped":
      return typeof input.progressPercent === "number"
        ? Math.min(100, Math.max(0, Math.round(input.progressPercent)))
        : 0;
    default:
      return 0;
  }
}

export function formatOtaBytes(received: number | null | undefined, total: number | null | undefined): string | null {
  if (typeof received !== "number" || typeof total !== "number" || total <= 0) {
    return null;
  }
  const fmt = (n: number) => {
    if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
    if (n >= 1024) return `${Math.round(n / 1024)} KB`;
    return `${n} B`;
  };
  return `${fmt(received)} / ${fmt(total)}`;
}
