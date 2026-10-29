import type { LmpHistoryEvent } from "../types/lmp";
import { lmpDateToTimestamp } from "./dates";
import { formatProcessStageLabel, isHistoryEngineeringFlow } from "./historyFormatting";

export type HistoryGlobalGanttSegment = {
  key: string;
  label: string;
  revision: string;
  leftPercent: number;
  widthPercent: number;
  isOpen: boolean;
  isLate: boolean;
  isEngineering: boolean;
  isCurrent: boolean;
};

export type HistoryGlobalGanttLayout = {
  rangeStartMs: number;
  rangeEndMs: number;
  segments: HistoryGlobalGanttSegment[];
};

function collectEventTimestamps(event: LmpHistoryEvent): number[] {
  const values: number[] = [];
  const start = lmpDateToTimestamp(event.start_date, event.start_time);
  const end = event.is_open
    ? Date.now()
    : lmpDateToTimestamp(event.end_date, event.end_time);
  const limit = lmpDateToTimestamp(event.limit_date, event.limit_time);

  if (start != null) values.push(start);
  if (end != null) values.push(end);
  if (limit != null) values.push(limit);

  return values;
}

function toPercent(value: number, rangeStartMs: number, rangeEndMs: number): number {
  const span = rangeEndMs - rangeStartMs;
  if (span <= 0) return 0;

  return Math.min(100, Math.max(0, ((value - rangeStartMs) / span) * 100));
}

export function buildHistoryGlobalGanttLayout(
  events: LmpHistoryEvent[],
): HistoryGlobalGanttLayout | null {
  if (events.length === 0) {
    return null;
  }

  const allTimestamps = events.flatMap((event) => collectEventTimestamps(event));
  if (allTimestamps.length === 0) {
    return null;
  }

  const rangeStartMs = Math.min(...allTimestamps);
  const rangeEndMs = Math.max(...allTimestamps);
  if (rangeEndMs <= rangeStartMs) {
    return null;
  }

  const segments = events
    .map((event, index) => {
      const start = lmpDateToTimestamp(event.start_date, event.start_time);
      if (start == null) return null;

      const end = event.is_open
        ? Date.now()
        : lmpDateToTimestamp(event.end_date, event.end_time) ?? start;
      const leftPercent = toPercent(start, rangeStartMs, rangeEndMs);
      const rightPercent = toPercent(end, rangeStartMs, rangeEndMs);
      const widthPercent = Math.max(0.8, Math.abs(rightPercent - leftPercent));

      return {
        key: `${event.revision}-${event.stage_code}-${index}`,
        label: formatProcessStageLabel(event.stage_code, event.stage_label),
        revision: event.revision?.trim() || "—",
        leftPercent: Math.min(leftPercent, rightPercent),
        widthPercent,
        isOpen: Boolean(event.is_open),
        isLate: Boolean(event.is_late),
        isEngineering: isHistoryEngineeringFlow(event),
        isCurrent: Boolean(event.is_current),
      };
    })
    .filter((segment): segment is HistoryGlobalGanttSegment => segment != null);

  if (segments.length === 0) {
    return null;
  }

  return { rangeStartMs, rangeEndMs, segments };
}
