/**
 * Period presets for Overview filters (Supplies).
 * Timezone: America/Sao_Paulo.
 */

export const PERIOD_PRESET_IDS = [
  "this_month",
  "last_month",
  "this_quarter",
  "this_year",
  "last_12_months",
  "custom",
] as const;

export type PeriodPresetId = (typeof PERIOD_PRESET_IDS)[number];

export type PeriodPresetRange = {
  from: string;
  to: string;
};

export const PERIOD_PRESET_OPTIONS: { value: PeriodPresetId; label: string }[] = [
  { value: "this_month", label: "Este mês" },
  { value: "last_month", label: "Mês passado" },
  { value: "this_quarter", label: "Este trimestre" },
  { value: "this_year", label: "Este ano" },
  { value: "last_12_months", label: "Últimos 12 meses" },
  { value: "custom", label: "Personalizado" },
];

const PAD2 = (n: number) => String(n).padStart(2, "0");

type Ymd = { y: number; m: number; d: number };

function parseYmd(iso: string): Ymd | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) return null;
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return null;
  return { y, m, d };
}

function formatYmd(y: number, m: number, d: number): string {
  return `${y}-${PAD2(m)}-${PAD2(d)}`;
}

function daysInMonth(y: number, m: number): number {
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}

export function todayIsoInTimeZone(
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const y = parts.find((p) => p.type === "year")?.value;
  const m = parts.find((p) => p.type === "month")?.value;
  const d = parts.find((p) => p.type === "day")?.value;
  if (!y || !m || !d) {
    return now.toISOString().slice(0, 10);
  }
  return `${y}-${m}-${d}`;
}

export function resolvePeriodPreset(
  preset: PeriodPresetId,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetRange | null {
  if (preset === "custom") return null;

  const today = todayIsoInTimeZone(now, timeZone);
  const parsed = parseYmd(today);
  if (!parsed) return null;
  const { y, m } = parsed;

  if (preset === "this_month") {
    return { from: formatYmd(y, m, 1), to: today };
  }

  if (preset === "last_month") {
    const ly = m === 1 ? y - 1 : y;
    const lm = m === 1 ? 12 : m - 1;
    return {
      from: formatYmd(ly, lm, 1),
      to: formatYmd(ly, lm, daysInMonth(ly, lm)),
    };
  }

  if (preset === "this_quarter") {
    const quarterStartMonth = Math.floor((m - 1) / 3) * 3 + 1;
    const quarterEndMonth = quarterStartMonth + 2;
    return {
      from: formatYmd(y, quarterStartMonth, 1),
      to: formatYmd(y, quarterEndMonth, daysInMonth(y, quarterEndMonth)),
    };
  }

  if (preset === "this_year") {
    return { from: formatYmd(y, 1, 1), to: today };
  }

  if (preset === "last_12_months") {
    const startY = m === 12 ? y : y - 1;
    const startM = m === 12 ? 1 : m + 1;
    return { from: formatYmd(startY, startM, 1), to: today };
  }

  return null;
}

export function parsePeriodPresetId(raw: string | null | undefined): PeriodPresetId | null {
  if (!raw) return null;
  return (PERIOD_PRESET_IDS as readonly string[]).includes(raw)
    ? (raw as PeriodPresetId)
    : null;
}
