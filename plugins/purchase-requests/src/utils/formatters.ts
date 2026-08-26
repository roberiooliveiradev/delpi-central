const LOOKBACK_DAYS = 90;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

export function defaultPeriod(): { date_from: string; date_to: string } {
  const end = new Date();
  end.setHours(0, 0, 0, 0);
  const start = new Date(end);
  start.setDate(start.getDate() - LOOKBACK_DAYS);
  return {
    date_from: formatIsoDate(start),
    date_to: formatIsoDate(end),
  };
}

/** Período amplo para catálogo admin de usuários Protheus (solicitantes em SC). */
export function adminProtheusUserPeriod(): { date_from: string; date_to: string } {
  const end = new Date();
  end.setHours(0, 0, 0, 0);
  const start = new Date(end);
  start.setDate(start.getDate() - 365);
  return {
    date_from: formatIsoDate(start),
    date_to: formatIsoDate(end),
  };
}

export function formatDatePtBr(iso: string | null | undefined): string {
  if (!iso) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 }).format(value);
}

export function computeDaysOpen(
  issueDate: string | null | undefined,
  overallStage: string | null | undefined,
): number | null {
  if (!issueDate) return null;
  if (overallStage === "completed" || overallStage === "residual_closed") return null;
  const start = new Date(`${issueDate}T00:00:00`);
  if (Number.isNaN(start.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffMs = today.getTime() - start.getTime();
  return Math.max(0, Math.floor(diffMs / 86_400_000));
}

export function truncateText(value: string, max: number): string {
  const trimmed = value.trim();
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, max - 1)}…`;
}
