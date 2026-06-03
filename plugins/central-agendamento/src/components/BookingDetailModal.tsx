import { format } from "date-fns";

import type { CalendarEvent } from "./BookingCalendar";
import { resourceTypeLabel } from "../constants/scheduling";

type Props = {
  open: boolean;
  event: CalendarEvent | null;
  canCancel: boolean;
  loading?: boolean;
  onClose: () => void;
  onCancel: () => Promise<void>;
};

export function BookingDetailModal({
  open,
  event,
  canCancel,
  loading = false,
  onClose,
  onCancel,
}: Props) {
  if (!open || !event) return null;

  async function handleCancel() {
    try {
      await onCancel();
      onClose();
    } catch {
      // erro tratado pelo pai
    }
  }

  return (
    <div className="ca-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="ca-modal ca-modal--compact"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ca-detail-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="ca-modal__header">
          <div>
            <p className="ca-modal__eyebrow">{resourceTypeLabel(event.resourceType)}</p>
            <h2 id="ca-detail-title">{event.title}</h2>
          </div>
          <button type="button" className="ca-icon-btn" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <dl className="ca-detail-list">
          <div>
            <dt>Recurso</dt>
            <dd>{event.resourceName}</dd>
          </div>
          <div>
            <dt>Responsável</dt>
            <dd>{event.bookedByName}</dd>
          </div>
          <div>
            <dt>Início</dt>
            <dd>{format(event.start, "dd/MM/yyyy HH:mm")}</dd>
          </div>
          <div>
            <dt>Término</dt>
            <dd>{format(event.end, "dd/MM/yyyy HH:mm")}</dd>
          </div>
          {event.notes ? (
            <div>
              <dt>Observações</dt>
              <dd>{event.notes}</dd>
            </div>
          ) : null}
        </dl>

        <div className="ca-modal__actions">
          <button type="button" className="ca-btn ca-btn--ghost" onClick={onClose}>
            Fechar
          </button>
          {canCancel ? (
            <button
              type="button"
              className="ca-btn ca-btn--danger"
              disabled={loading}
              onClick={() => void handleCancel()}
            >
              {loading ? "Cancelando..." : "Cancelar reserva"}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
