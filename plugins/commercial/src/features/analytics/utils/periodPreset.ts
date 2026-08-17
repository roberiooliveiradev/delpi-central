/**
 * Period presets for analytics filters (Overview / OTD / opportunities).
 * Timezone: America/Sao_Paulo — calendar date in that zone.
 */

export const PERIOD_PRESET_IDS = [
  "today",
  "this_week",
  "this_month",
  "last_month",
  "this_quarter",
  "this_year",
  "last_12_months",
  "custom",
] as const;

export type PeriodPresetId = (typeof PERIOD_PRESET_IDS)[number];

export type PeriodPresetRange = {
  dateStart: string;
  dateEnd: string;
  competence: string;
};

export const PERIOD_PRESET_OPTIONS: {
  value: PeriodPresetId;
  label: string;
}[] = [
  { value: "today", label: "Hoje" },
  { value: "this_week", label: "Esta semana" },
  { value: "this_month", label: "Este mês" },
  { value: "last_month", label: "Mês passado" },
  { value: "this_quarter", label: "Este trimestre" },
  { value: "this_year", label: "Este ano" },
  { value: "last_12_months", label: "Últimos 12 meses" },
  { value: "custom", label: "Personalizado" },
];

/** Presets that resolve a concrete date range (excludes custom). */
export type ResolvedPeriodPresetId = Exclude<PeriodPresetId, "custom">;

const RESOLVED_PRESET_IDS: ResolvedPeriodPresetId[] = [
  "today",
  "this_week",
  "this_month",
  "last_month",
  "this_quarter",
  "this_year",
  "last_12_months",
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

/** Last calendar day of month (1–12). */
function daysInMonth(y: number, m: number): number {
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}

/** Add days to a Y-M-D string (Gregorian). */
function addCalendarDays(iso: string, deltaDays: number): string {
  const parsed = parseYmd(iso);
  if (!parsed) return iso;
  const utc = Date.UTC(parsed.y, parsed.m - 1, parsed.d + deltaDays);
  const dt = new Date(utc);
  return formatYmd(dt.getUTCFullYear(), dt.getUTCMonth() + 1, dt.getUTCDate());
}

/** Calendar Y-M-D in America/Sao_Paulo for the given instant. */
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

/** Weekday in zone: 0 = Sunday … 6 = Saturday. */
function weekdayInTimeZone(now: Date, timeZone: string): number {
  const label = new Intl.DateTimeFormat("en-US", {
    timeZone,
    weekday: "short",
  }).format(now);
  const map: Record<string, number> = {
    Sun: 0,
    Mon: 1,
    Tue: 2,
    Wed: 3,
    Thu: 4,
    Fri: 5,
    Sat: 6,
  };
  return map[label] ?? 0;
}

/**
 * Resolve date range for a preset.
 * - today / this_week / this_month / this_quarter / this_year → até hoje
 * - last_month → mês civil anterior completo
 * - last_12_months → 1º dia do mês há 11 meses → hoje
 * - custom → null (caller keeps current dates)
 */
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

  if (preset === "today") {
    return { dateStart: today, dateEnd: today, competence: `${y}-${PAD2(m)}` };
  }

  if (preset === "this_week") {
    const weekday = weekdayInTimeZone(now, timeZone);
    const mondayOffset = weekday === 0 ? -6 : 1 - weekday;
    const dateStart = addCalendarDays(today, mondayOffset);
    return { dateStart, dateEnd: today, competence: "" };
  }

  if (preset === "this_month") {
    return {
      dateStart: formatYmd(y, m, 1),
      dateEnd: today,
      competence: `${y}-${PAD2(m)}`,
    };
  }

  if (preset === "last_month") {
    const ly = m === 1 ? y - 1 : y;
    const lm = m === 1 ? 12 : m - 1;
    return {
      dateStart: formatYmd(ly, lm, 1),
      dateEnd: formatYmd(ly, lm, daysInMonth(ly, lm)),
      competence: `${ly}-${PAD2(lm)}`,
    };
  }

  if (preset === "this_quarter") {
    const qm = Math.floor((m - 1) / 3) * 3 + 1;
    return {
      dateStart: formatYmd(y, qm, 1),
      dateEnd: today,
      competence: "",
    };
  }

  if (preset === "this_year") {
    return {
      dateStart: formatYmd(y, 1, 1),
      dateEnd: today,
      competence: "",
    };
  }

  // last_12_months — first day of month 11 months ago through today
  const startMonthIndex = y * 12 + (m - 1) - 11;
  const sy = Math.floor(startMonthIndex / 12);
  const sm = (startMonthIndex % 12) + 1;
  return {
    dateStart: formatYmd(sy, sm, 1),
    dateEnd: today,
    competence: "",
  };
}

/** Infer which preset matches the current range (or custom). */
export function detectPeriodPreset(
  dateStart: string,
  dateEnd: string,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetId {
  for (const id of RESOLVED_PRESET_IDS) {
    const range = resolvePeriodPreset(id, now, timeZone);
    if (range && dateStart === range.dateStart && dateEnd === range.dateEnd) {
      return id;
    }
  }
  return "custom";
}

/** Chip curto MTD/YTD para cards Overview (ata §5). */
export type PeriodKindChip = "MTD" | "YTD";

export function resolvePeriodKindChip(
  preset: PeriodPresetId | null | undefined,
): PeriodKindChip | null {
  switch (preset) {
    case "this_month":
      return "MTD";
    case "this_year":
    case "last_12_months":
      return "YTD";
    default:
      return null;
  }
}
