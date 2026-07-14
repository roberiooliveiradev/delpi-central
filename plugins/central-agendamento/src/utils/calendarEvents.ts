import {
  addDays,
  format,
  isSameDay,
  max,
  min,
  setHours,
  startOfDay,
} from "date-fns";

import type { BookingStatus, ResourceType } from "../constants/scheduling";

export const CALENDAR_DAY_START_HOUR = 7;
export const CALENDAR_DAY_END_HOUR = 20;

export type MultiDaySegmentMeta = {
  isFirst: boolean;
  isLast: boolean;
  isMiddle: boolean;
};

export type CalendarEvent = {
  id: string;
  bookingId: string;
  title: string;
  start: Date;
  end: Date;
  originalStart: Date;
  originalEnd: Date;
  resourceId: string;
  resourceName: string;
  resourceType: ResourceType;
  bookedByName: string;
  notes: string | null;
  bookedByUserId: string;
  status: BookingStatus;
  decidedByName?: string | null;
  decisionReason?: string | null;
  expiresAt?: string | null;
  recurrenceSeriesId?: string | null;
  recurrenceFrequency?: "weekly" | "monthly" | null;
  multiDaySegment?: MultiDaySegmentMeta;
};

export function isMultiDayBooking(start: Date, end: Date): boolean {
  return !isSameDay(start, end);
}

export function resolveBookingId(eventId: string): string {
  const [bookingId] = eventId.split("__");
  return bookingId ?? eventId;
}

function dayGridBounds(date: Date): { min: Date; max: Date } {
  const day = startOfDay(date);
  return {
    min: setHours(day, CALENDAR_DAY_START_HOUR),
    max: setHours(day, CALENDAR_DAY_END_HOUR),
  };
}

/** Divide reservas multi-dia em blocos diários na grade horária (semana/dia). */
export function expandMultiDayEventForTimeGrid(event: CalendarEvent): CalendarEvent[] {
  if (!isMultiDayBooking(event.originalStart, event.originalEnd)) {
    return [event];
  }

  const segments: CalendarEvent[] = [];
  let cursor = startOfDay(event.originalStart);
  const lastDay = startOfDay(event.originalEnd);

  while (cursor <= lastDay) {
    const { min: gridMin, max: gridMax } = dayGridBounds(cursor);

    let segmentStart: Date;
    let segmentEnd: Date;

    if (isSameDay(cursor, event.originalStart) && isSameDay(cursor, event.originalEnd)) {
      segmentStart = event.originalStart;
      segmentEnd = event.originalEnd;
    } else if (isSameDay(cursor, event.originalStart)) {
      segmentStart = event.originalStart;
      segmentEnd = gridMax;
    } else if (isSameDay(cursor, event.originalEnd)) {
      segmentStart = gridMin;
      segmentEnd = event.originalEnd;
    } else {
      segmentStart = gridMin;
      segmentEnd = gridMax;
    }

    segmentStart = max([max([segmentStart, gridMin]), event.originalStart]);
    segmentEnd = min([min([segmentEnd, gridMax]), event.originalEnd]);

    if (segmentEnd > segmentStart) {
      const isFirst = isSameDay(cursor, event.originalStart);
      const isLast = isSameDay(cursor, event.originalEnd);
      segments.push({
        ...event,
        id: `${event.bookingId}__${format(cursor, "yyyy-MM-dd")}`,
        start: segmentStart,
        end: segmentEnd,
        multiDaySegment: {
          isFirst,
          isLast,
          isMiddle: !isFirst && !isLast,
        },
      });
    }

    cursor = addDays(cursor, 1);
  }

  return segments.length > 0 ? segments : [event];
}

export function segmentEventClassName(event: CalendarEvent): string {
  const segment = event.multiDaySegment;
  if (!segment || (segment.isFirst && segment.isLast)) {
    return "ca-cal-event--single";
  }
  if (segment.isFirst) return "ca-cal-event--seg-start";
  if (segment.isLast) return "ca-cal-event--seg-end";
  return "ca-cal-event--seg-middle";
}
