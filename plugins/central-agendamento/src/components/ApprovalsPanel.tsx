import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { format } from "date-fns";

import type { SchedulingBooking } from "../api/schedulingApi";
import { BOOKING_STATUS_LABELS } from "../constants/scheduling";

type Props = {
  bookings: SchedulingBooking[];
  highlightBookingId?: string | null;
  loading?: boolean;
  actionLoading?: boolean;
  onApprove: (bookingId: string) => Promise<void>;
  onReject: (bookingId: string, reason: string) => Promise<void>;
  onRefresh: () => void;
};

export function ApprovalsPanel({
  bookings,
  highlightBookingId,
  loading = false,
  actionLoading = false,
  onApprove,
  onReject,
  onRefresh,
}: Props) {
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!highlightBookingId) return;
    const el = document.getElementById(`ca-approval-${highlightBookingId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightBookingId, bookings]);

  async function handleApprove(bookingId: string) {
    setError(null);
    try {
      await onApprove(bookingId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao confirmar.");
    }
  }

  async function handleReject(bookingId: string) {
    setError(null);
    if (reason.trim().length < 3) {
      setError("Informe o motivo da rejeição (mínimo 3 caracteres).");
      return;
    }
    try {
      await onReject(bookingId, reason.trim());
      setRejectingId(null);
      setReason("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao rejeitar.");
    }
  }

  return (
    <div className="ca-approvals">
      <div className="ca-approvals__header">
        <div>
          <h2>Aprovações pendentes</h2>
          <p>Confirme ou rejeite solicitações que exigem autorização prévia.</p>
        </div>
        <button type="button" className="ca-btn ca-btn--ghost" onClick={onRefresh}>
          Atualizar fila
        </button>
      </div>

      {error ? <div className="ca-alert ca-alert--error">{error}</div> : null}

      {loading ? <div className="ca-loading">Carregando pendências...</div> : null}

      {!loading && bookings.length === 0 ? (
        <div className="ca-empty-state">Nenhuma solicitação aguardando aprovação.</div>
      ) : null}

      <ul className="ca-approvals__list">
        {bookings.map((booking) => {
          const isHighlight = booking.id === highlightBookingId;
          const isRejecting = rejectingId === booking.id;
          return (
            <li
              key={booking.id}
              id={`ca-approval-${booking.id}`}
              className={`ca-approvals__item${isHighlight ? " ca-approvals__item--highlight" : ""}`}
            >
              <div className="ca-approvals__item-main">
                <div>
                  <p className="ca-approvals__title">{booking.title}</p>
                  <p className="ca-approvals__meta">
                    {booking.resource_name ?? "Recurso"} · {booking.booked_by_name}
                  </p>
                  <p className="ca-approvals__meta">
                    {format(new Date(booking.start_at), "dd/MM/yyyy HH:mm")} —{" "}
                    {format(new Date(booking.end_at), "dd/MM/yyyy HH:mm")}
                  </p>
                  {booking.expires_at ? (
                    <p className="ca-approvals__meta">
                      Expira em {format(new Date(booking.expires_at), "dd/MM/yyyy HH:mm")}
                    </p>
                  ) : null}
                  <span className="ca-status-badge ca-status-badge--pending">
                    {BOOKING_STATUS_LABELS.pending}
                  </span>
                </div>
                <div className="ca-approvals__actions">
                  <button
                    type="button"
                    className="ca-btn ca-btn--primary"
                    disabled={actionLoading}
                    onClick={() => void handleApprove(booking.id)}
                  >
                    <Check size={16} />
                    Confirmar
                  </button>
                  <button
                    type="button"
                    className="ca-btn ca-btn--ghost"
                    disabled={actionLoading}
                    onClick={() => {
                      setRejectingId(isRejecting ? null : booking.id);
                      setReason("");
                      setError(null);
                    }}
                  >
                    <X size={16} />
                    Rejeitar
                  </button>
                </div>
              </div>

              {isRejecting ? (
                <div className="ca-approvals__reject">
                  <label htmlFor={`ca-reject-reason-${booking.id}`}>Motivo da rejeição</label>
                  <textarea
                    id={`ca-reject-reason-${booking.id}`}
                    value={reason}
                    onChange={(event) => setReason(event.target.value)}
                    rows={3}
                    placeholder="Explique o motivo para o solicitante..."
                  />
                  <div className="ca-modal__actions">
                    <button
                      type="button"
                      className="ca-btn ca-btn--ghost"
                      onClick={() => setRejectingId(null)}
                    >
                      Cancelar
                    </button>
                    <button
                      type="button"
                      className="ca-btn ca-btn--danger"
                      disabled={actionLoading}
                      onClick={() => void handleReject(booking.id)}
                    >
                      Confirmar rejeição
                    </button>
                  </div>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
