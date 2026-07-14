import { useEffect, useMemo, useState } from "react";
import { CalendarClock, CalendarX2, Filter } from "lucide-react";
import { format } from "date-fns";

import type { SchedulingBooking } from "../api/schedulingApi";
import {
  BOOKING_STATUS_LABELS,
  type BookingStatus,
} from "../constants/scheduling";

type StatusFilter = "all" | BookingStatus;

type Props = {
  bookings: SchedulingBooking[];
  highlightBookingId?: string | null;
  loading?: boolean;
  actionLoading?: boolean;
  onRefresh: () => void;
  onCancel: (bookingId: string) => Promise<void>;
};

const FILTERS: Array<{ value: StatusFilter; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "pending", label: "Aguardando" },
  { value: "confirmed", label: "Confirmadas" },
  { value: "rejected", label: "Rejeitadas" },
  { value: "expired", label: "Expiradas" },
  { value: "cancelled", label: "Canceladas" },
];

function formatBookingWindow(startAt: string, endAt: string): string {
  const start = new Date(startAt);
  const end = new Date(endAt);
  const sameDay =
    start.getFullYear() === end.getFullYear() &&
    start.getMonth() === end.getMonth() &&
    start.getDate() === end.getDate();
  if (sameDay) {
    return `${format(start, "dd/MM/yyyy")} · ${format(start, "HH:mm")} – ${format(end, "HH:mm")}`;
  }
  return `${format(start, "dd/MM/yyyy HH:mm")} – ${format(end, "dd/MM/yyyy HH:mm")}`;
}

function statusHint(booking: SchedulingBooking): string | null {
  if (booking.status === "pending" && booking.expires_at) {
    return `Aguarde aprovação até ${format(new Date(booking.expires_at), "dd/MM/yyyy HH:mm")}.`;
  }
  if (booking.status === "rejected") {
    const who = booking.decided_by_name ? ` por ${booking.decided_by_name}` : "";
    const reason = booking.decision_reason?.trim();
    return reason ? `Rejeitada${who}: ${reason}` : `Rejeitada${who}.`;
  }
  if (booking.status === "confirmed" && booking.decided_by_name) {
    return `Confirmada por ${booking.decided_by_name}.`;
  }
  if (booking.status === "expired") {
    return "Expirou sem aprovação até o início do horário.";
  }
  if (booking.status === "cancelled") {
    return "Você cancelou esta reserva.";
  }
  return null;
}

export function MyBookingsPanel({
  bookings,
  highlightBookingId,
  loading = false,
  actionLoading = false,
  onRefresh,
  onCancel,
}: Props) {
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!highlightBookingId) return;
    const el = document.getElementById(`ca-mine-${highlightBookingId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightBookingId, bookings]);

  const counts = useMemo(() => {
    const base: Record<BookingStatus, number> = {
      pending: 0,
      confirmed: 0,
      rejected: 0,
      expired: 0,
      cancelled: 0,
    };
    for (const booking of bookings) {
      base[booking.status] += 1;
    }
    return base;
  }, [bookings]);

  const filtered = useMemo(() => {
    if (filter === "all") return bookings;
    return bookings.filter((booking) => booking.status === filter);
  }, [bookings, filter]);

  async function handleCancel(bookingId: string) {
    setError(null);
    try {
      await onCancel(bookingId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao cancelar reserva.");
    }
  }

  return (
    <div className="ca-mine">
      <div className="ca-mine__header">
        <div>
          <h2>Minhas reservas</h2>
          <p>Acompanhe suas solicitações e o estado de cada uma nesta filial.</p>
        </div>
        <button type="button" className="ca-btn ca-btn--ghost" onClick={onRefresh}>
          Atualizar
        </button>
      </div>

      <div className="ca-mine__filters" role="toolbar" aria-label="Filtrar por status">
        <span className="ca-mine__filters-label">
          <Filter size={14} aria-hidden="true" />
          Status
        </span>
        {FILTERS.map((item) => {
          const count =
            item.value === "all"
              ? bookings.length
              : counts[item.value as BookingStatus];
          return (
            <button
              key={item.value}
              type="button"
              className={`ca-chip${filter === item.value ? " ca-chip--active" : ""}`}
              onClick={() => setFilter(item.value)}
            >
              {item.label}
              <span className="ca-chip__count">{count}</span>
            </button>
          );
        })}
      </div>

      {error ? <div className="ca-alert ca-alert--error">{error}</div> : null}

      {loading ? <div className="ca-loading">Carregando suas reservas...</div> : null}

      {!loading && filtered.length === 0 ? (
        <div className="ca-empty-state">
          {bookings.length === 0
            ? "Você ainda não tem reservas nesta filial."
            : "Nenhuma reserva neste filtro."}
        </div>
      ) : null}

      <ul className="ca-mine__list">
        {filtered.map((booking) => {
          const isHighlight = booking.id === highlightBookingId;
          const canCancel = booking.status === "pending" || booking.status === "confirmed";
          const hint = statusHint(booking);
          return (
            <li
              key={booking.id}
              id={`ca-mine-${booking.id}`}
              className={`ca-mine__item ca-mine__item--${booking.status}${
                isHighlight ? " ca-mine__item--highlight" : ""
              }`}
            >
              <div className="ca-mine__item-main">
                <div className="ca-mine__body">
                  <div className="ca-mine__title-row">
                    <p className="ca-mine__title">{booking.title}</p>
                    <span className={`ca-status-badge ca-status-badge--${booking.status}`}>
                      {BOOKING_STATUS_LABELS[booking.status]}
                    </span>
                  </div>
                  <p className="ca-mine__resource">{booking.resource_name ?? "Recurso"}</p>

                  <div className="ca-mine__fact">
                    <CalendarClock size={18} aria-hidden="true" />
                    <div>
                      <span className="ca-mine__fact-label">Horário</span>
                      <strong className="ca-mine__fact-value">
                        {formatBookingWindow(booking.start_at, booking.end_at)}
                      </strong>
                    </div>
                  </div>

                  {hint ? <p className="ca-mine__hint">{hint}</p> : null}
                </div>

                {canCancel ? (
                  <div className="ca-mine__actions">
                    <button
                      type="button"
                      className="ca-btn ca-btn--ghost"
                      disabled={actionLoading}
                      onClick={() => void handleCancel(booking.id)}
                    >
                      <CalendarX2 size={16} />
                      Cancelar
                    </button>
                  </div>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
