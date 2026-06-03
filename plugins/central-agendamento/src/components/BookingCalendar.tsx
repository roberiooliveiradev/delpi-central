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
import "react-big-calendar/lib/css/react-big-calendar.css";

const locales = { "pt-BR": ptBR };

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 0 }),
  getDay,
  locales,
});

export type CalendarEvent = {
  id: string;
  title: string;
  start: Date;
  end: Date;
  resourceId: string;
  resourceName: string;
  resourceType: SchedulingResource["resource_type"];
  bookedByName: string;
  notes: string | null;
  bookedByUserId: string;
};

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
  return {
    id: booking.id,
    title: booking.title,
    start: new Date(booking.start_at),
    end: new Date(booking.end_at),
    resourceId: booking.resource_id,
    resourceName,
    resourceType,
    bookedByName: booking.booked_by_name,
    notes: booking.notes,
    bookedByUserId: booking.booked_by_user_id,
  };
}

function CalendarEventBlock({ event }: EventProps<CalendarEvent>) {
  return (
    <div className="ca-cal-event">
      <span className="ca-cal-event__resource">{event.resourceName}</span>
      <span className="ca-cal-event__title">{event.title}</span>
      <span className="ca-cal-event__meta">{event.bookedByName}</span>
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
  const events = useMemo(
    () => bookings.map((booking) => toEvent(booking, resources)),
    [bookings, resources],
  );

  const eventStyleGetter = (event: CalendarEvent) => {
    const color = RESOURCE_TYPE_COLORS[event.resourceType];
    return {
      style: {
        backgroundColor: color,
        borderColor: color,
        color: "#fff",
        borderRadius: "6px",
        border: "none",
        fontSize: "11px",
        padding: "2px 4px",
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
        min={new Date(1970, 0, 1, 7, 0, 0)}
        max={new Date(1970, 0, 1, 20, 0, 0)}
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
          event: CalendarEventBlock,
        }}
        eventPropGetter={eventStyleGetter}
        onSelectEvent={(event) => onSelectEvent(event as CalendarEvent)}
        onSelectSlot={onSelectSlot}
        tooltipAccessor={(event) => {
          const item = event as CalendarEvent;
          return `${item.resourceName}\n${item.title}\n${resourceTypeLabel(item.resourceType)} · ${item.bookedByName}`;
        }}
      />
    </div>
  );
}

export type { SlotInfo, View };
