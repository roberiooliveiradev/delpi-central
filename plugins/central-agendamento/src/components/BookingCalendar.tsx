import { useMemo } from "react";
import {
  Calendar as BigCalendar,
  dateFnsLocalizer,
  type EventProps,
  type SlotInfo,
  type View,
} from "react-big-calendar";
import { format, getDay, parse, startOfWeek } from "date-fns";
import { ptBR } from "date-fns/locale";

import type { SchedulingBooking, SchedulingResource } from "../api/schedulingApi";
import { RESOURCE_TYPE_COLORS, resourceTypeLabel } from "../constants/scheduling";
import {
  CALENDAR_DAY_END_HOUR,
  CALENDAR_DAY_START_HOUR,
  expandMultiDayEventForTimeGrid,
  segmentEventClassName,
  type CalendarEvent,
} from "../utils/calendarEvents";
import { CalendarDayHeader, CalendarMonthDateHeader } from "./CalendarHeaders";
import "react-big-calendar/lib/css/react-big-calendar.css";

const locales = { "pt-BR": ptBR };

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 0 }),
  getDay,
  locales,
});

export type { CalendarEvent };

type Props = {
  bookings: SchedulingBooking[];
  resources: SchedulingResource[];
  currentDate: Date;
  view: View;
  onViewChange: (view: View) => void;
  onNavigate: (date: Date) => void;
  onSelectEvent: (event: CalendarEvent) => void;
  onSelectSlot: (slot: SlotInfo) => void;
};

function toEvent(booking: SchedulingBooking, resources: SchedulingResource[]): CalendarEvent {
  const resource = resources.find((item) => item.id === booking.resource_id);
  const resourceType = booking.resource_type ?? resource?.resource_type ?? "other";
  const resourceName = booking.resource_name ?? resource?.name ?? "Recurso";
  const start = new Date(booking.start_at);
  const end = new Date(booking.end_at);

  return {
    id: booking.id,
    bookingId: booking.id,
    title: booking.title,
    start,
    end,
    originalStart: start,
    originalEnd: end,
    resourceId: booking.resource_id,
    resourceName,
    resourceType,
    bookedByName: booking.booked_by_name,
    notes: booking.notes,
    bookedByUserId: booking.booked_by_user_id,
    status: booking.status,
    decidedByName: booking.decided_by_name,
    decisionReason: booking.decision_reason,
    expiresAt: booking.expires_at,
    recurrenceSeriesId: booking.recurrence_series_id,
    recurrenceFrequency: booking.recurrence_frequency,
  };
}

function CalendarEventBlock({ event }: EventProps<CalendarEvent>) {
  const segment = event.multiDaySegment;
  const showDetails = !segment?.isMiddle;
  const isRecurring = Boolean(event.recurrenceSeriesId);

  return (
    <div className={`ca-cal-event${segment?.isMiddle ? " ca-cal-event--middle-day" : ""}`}>
      {showDetails ? (
        <>
          <span className="ca-cal-event__resource">
            {isRecurring ? <span className="ca-cal-event__repeat" aria-hidden="true">↻ </span> : null}
            {event.resourceName}
          </span>
          <span className="ca-cal-event__title">{event.title}</span>
          <span className="ca-cal-event__meta ca-cal-event__meta--who">
            {event.status === "pending" ? "Pend. · " : ""}
            {event.bookedByName}
          </span>
          <span className="ca-cal-event__meta ca-cal-event__meta--when">
            {format(event.originalStart, "HH:mm")}–{format(event.originalEnd, "HH:mm")}
          </span>
        </>
      ) : (
        <>
          <span className="ca-cal-event__title">{event.title}</span>
          <span className="ca-cal-event__meta ca-cal-event__meta--continues">Continua</span>
        </>
      )}
    </div>
  );
}

export function BookingCalendar({
  bookings,
  resources,
  currentDate,
  view,
  onViewChange,
  onNavigate,
  onSelectEvent,
  onSelectSlot,
}: Props) {
  const events = useMemo(() => {
    const base = bookings.map((booking) => toEvent(booking, resources));
    if (view === "month") return base;
    return base.flatMap((event) => expandMultiDayEventForTimeGrid(event));
  }, [bookings, resources, view]);

  const eventStyleGetter = (event: CalendarEvent) => {
    const baseColor = RESOURCE_TYPE_COLORS[event.resourceType];
    const color = event.status === "pending" ? "#b45309" : baseColor;
    const segment = event.multiDaySegment;
    const isSingleDaySegment = !segment || (segment.isFirst && segment.isLast);

    return {
      className: `${segmentEventClassName(event)}${event.status === "pending" ? " ca-cal-event--pending" : ""}`,
      style: {
        backgroundColor: color,
        borderColor: color,
        color: "#fff",
        border: event.status === "pending" ? "1px dashed rgba(255,255,255,0.7)" : "none",
        fontSize: "11px",
        padding: "4px 6px",
        opacity: event.status === "pending" ? 0.92 : 1,
        ...(isSingleDaySegment ? { borderRadius: "6px" } : {}),
      },
    };
  };

  return (
    <div className="ca-calendar-wrap">
      <BigCalendar
        localizer={localizer}
        culture="pt-BR"
        events={events}
        date={currentDate}
        view={view}
        views={["month", "week", "day"]}
        onView={onViewChange}
        onNavigate={onNavigate}
        startAccessor="start"
        endAccessor="end"
        dayLayoutAlgorithm="no-overlap"
        selectable
        popup
        step={30}
        timeslots={2}
        min={new Date(1970, 0, 1, CALENDAR_DAY_START_HOUR, 0, 0)}
        max={new Date(1970, 0, 1, CALENDAR_DAY_END_HOUR, 0, 0)}
        showMultiDayTimes
        allDayMaxRows={0}
        messages={{
          today: "Hoje",
          previous: "Anterior",
          next: "Próximo",
          month: "Mês",
          week: "Semana",
          day: "Dia",
          agenda: "Agenda",
          noEventsInRange: "Nenhuma reserva neste período.",
        }}
        components={{
          header: CalendarDayHeader,
          month: {
            dateHeader: CalendarMonthDateHeader,
          },
          event: CalendarEventBlock,
        }}
        eventPropGetter={eventStyleGetter}
        onSelectEvent={(event) => onSelectEvent(event as CalendarEvent)}
        onSelectSlot={onSelectSlot}
        tooltipAccessor={(event) => {
          const item = event as CalendarEvent;
          const startLabel = format(item.originalStart, "dd/MM/yyyy HH:mm");
          const endLabel = format(item.originalEnd, "dd/MM/yyyy HH:mm");
          return `${item.resourceName}\n${item.title}\nQuem: ${item.bookedByName}\nHorário: ${startLabel} — ${endLabel}\n${resourceTypeLabel(item.resourceType)}`;
        }}
      />
    </div>
  );
}

export type { SlotInfo, View };
