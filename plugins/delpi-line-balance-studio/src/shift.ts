import type { ValidationIssue, ValidationResult } from "./validation.js";

type ClockInterval = Readonly<{ start: string; end: string }>;

export type ShiftInput =
  | Readonly<{ mode: "CLOCK"; start: string; end: string; breaks: readonly ClockInterval[] }>
  | Readonly<{ mode: "MINUTES"; durationMinutes: number; breaks: readonly number[] }>;

export type ShiftSummary = Readonly<{
  grossMinutes: number;
  breakMinutes: number;
  productiveMinutes: number;
  provenance: "CALCULATED";
}>;

const minutesPerDay = 24 * 60;

function clockMinutes(value: string): number | null {
  if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value)) return null;
  return Number(value.slice(0, 2)) * 60 + Number(value.slice(3));
}

function finishShift(grossMinutes: number, breakMinutes: number): ValidationResult<ShiftSummary> {
  const productiveMinutes = grossMinutes - breakMinutes;
  if (productiveMinutes <= 0) {
    return { ok: false, issues: [{ path: "breaks", code: "NO_PRODUCTIVE_TIME" }] };
  }
  return {
    ok: true,
    value: { grossMinutes, breakMinutes, productiveMinutes, provenance: "CALCULATED" },
  };
}

export function summarizeShift(input: ShiftInput): ValidationResult<ShiftSummary> {
  const issues: ValidationIssue[] = [];
  if (input.mode === "MINUTES") {
    if (!Number.isInteger(input.durationMinutes) || input.durationMinutes <= 0 ||
        input.durationMinutes > minutesPerDay) {
      issues.push({ path: "durationMinutes", code: "INVALID_NUMBER" });
    }
    let breakMinutes = 0;
    input.breaks.forEach((duration, index) => {
      if (!Number.isInteger(duration) || duration <= 0 || duration > minutesPerDay) {
        issues.push({ path: `breaks[${index}]`, code: "INVALID_NUMBER" });
      } else {
        breakMinutes += duration;
      }
    });
    if (issues.length) return { ok: false, issues };
    return finishShift(input.durationMinutes, breakMinutes);
  }

  const start = clockMinutes(input.start);
  const end = clockMinutes(input.end);
  if (start === null) issues.push({ path: "start", code: "INVALID_CLOCK_TIME" });
  if (end === null) issues.push({ path: "end", code: "INVALID_CLOCK_TIME" });
  if (start === null || end === null) return { ok: false, issues };
  if (start === end) return { ok: false, issues: [{ path: "end", code: "AMBIGUOUS_SHIFT" }] };

  const shiftEnd = end < start ? end + minutesPerDay : end;
  const intervals: { start: number; end: number; path: string }[] = [];

  input.breaks.forEach((pause, index) => {
    const path = `breaks[${index}]`;
    const pauseStart = clockMinutes(pause.start);
    const pauseEnd = clockMinutes(pause.end);
    if (pauseStart === null) issues.push({ path: `${path}.start`, code: "INVALID_CLOCK_TIME" });
    if (pauseEnd === null) issues.push({ path: `${path}.end`, code: "INVALID_CLOCK_TIME" });
    if (pauseStart === null || pauseEnd === null) return;
    if (pauseStart === pauseEnd) {
      issues.push({ path, code: "EMPTY_BREAK" });
      return;
    }

    const absoluteStart = pauseStart < start ? pauseStart + minutesPerDay : pauseStart;
    const duration = (pauseEnd - pauseStart + minutesPerDay) % minutesPerDay;
    const absoluteEnd = absoluteStart + duration;
    if (absoluteEnd > shiftEnd) {
      issues.push({ path, code: "BREAK_OUTSIDE_SHIFT" });
      return;
    }
    intervals.push({ start: absoluteStart, end: absoluteEnd, path });
  });

  let previousEnd = start;
  let breakMinutes = 0;
  for (const interval of intervals.sort((a, b) => a.start - b.start)) {
    if (interval.start < previousEnd) {
      issues.push({ path: interval.path, code: "BREAK_OVERLAP" });
    }
    previousEnd = Math.max(previousEnd, interval.end);
    breakMinutes += interval.end - interval.start;
  }

  if (issues.length) return { ok: false, issues };
  return finishShift(shiftEnd - start, breakMinutes);
}
