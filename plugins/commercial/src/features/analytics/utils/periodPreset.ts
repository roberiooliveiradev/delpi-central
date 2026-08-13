/**
 * Period presets for analytics Overview (MTD / YTD / custom).
 * Timezone: America/Sao_Paulo — calendar date in that zone.
 */

export type PeriodPresetId = "mtd" | "ytd" | "custom";

export type PeriodPresetRange = {
  dateStart: string;
  dateEnd: string;
  competence: string;
};

const PAD2 = (n: number) => String(n).padStart(2, "0");

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

/**
 * Resolve date range for a preset.
 * - mtd: first day of current month → today
 * - ytd: Jan 1 of current year → today
 * - custom: leave dates unchanged (caller keeps current)
 */
export function resolvePeriodPreset(
  preset: PeriodPresetId,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetRange | null {
  if (preset === "custom") return null;
  const today = todayIsoInTimeZone(now, timeZone);
  const [y, m] = today.split("-").map(Number);
  if (preset === "mtd") {
    const dateStart = `${y}-${PAD2(m)}-01`;
    return {
      dateStart,
      dateEnd: today,
      competence: `${y}-${PAD2(m)}`,
    };
  }
  // ytd
  const dateStart = `${y}-01-01`;
  return {
    dateStart,
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
  const mtd = resolvePeriodPreset("mtd", now, timeZone);
  const ytd = resolvePeriodPreset("ytd", now, timeZone);
  if (mtd && dateStart === mtd.dateStart && dateEnd === mtd.dateEnd) return "mtd";
  if (ytd && dateStart === ytd.dateStart && dateEnd === ytd.dateEnd) return "ytd";
  return "custom";
}
