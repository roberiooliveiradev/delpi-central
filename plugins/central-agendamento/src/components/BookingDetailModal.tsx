import { format } from "date-fns";
import { ArrowRight, CalendarX, ListX, Repeat } from "lucide-react";
import { useEffect, useState } from "react";

import type { CancelScope } from "../api/schedulingApi";
import type { CalendarEvent } from "./BookingCalendar";
import { BOOKING_STATUS_LABELS, resourceTypeLabel } from "../constants/scheduling";

type Props = {
  open: boolean;
  event: CalendarEvent | null;
  canCancel: boolean;
  loading?: boolean;
  onClose: () => void;
  onCancel: (scope: CancelScope) => Promise<void>;
};

const CANCEL_SCOPE_CHOICES: Array<{
  scope: CancelScope;
  label: string;
  hint: string;
  icon: typeof CalendarX;
}> = [
  { scope: "occurrence", label: "Somente esta ocorrência", hint: "Mantém as demais da série", icon: CalendarX },
  { scope: "future", label: "Esta e as futuras", hint: "Cancela desta data em diante", icon: ArrowRight },
  { scope: "all", label: "Toda a série", hint: "Remove todas as ocorrências", icon: ListX },
];

export function BookingDetailModal({
  open,
  event,
  canCancel,
  loading = false,
  onClose,
  onCancel,
}: Props) {
  const [cancelScope, setCancelScope] = useState<CancelScope>("occurrence");
  const [showCancelOptions, setShowCancelOptions] = useState(false);

  useEffect(() => {
    if (!open) {
      setShowCancelOptions(false);
      setCancelScope("occurrence");
    }
  }, [open, event?.bookingId]);

  if (!open || !event) return null;

  const isRecurring = Boolean(event.recurrenceSeriesId);

  const frequencyLabels = {
    weekly: "Semanal",
    monthly: "Mensal",
  } as const;

  async function handleCancel() {
    try {
      await onCancel(cancelScope);
      onClose();
    } catch {
      // erro tratado pelo pai
    }
  }

  function openCancelFlow() {
    if (isRecurring) {
      setCancelScope("occurrence");
      setShowCancelOptions(true);
      return;
    }
    void handleCancel();
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
            {isRecurring && event.recurrenceFrequency ? (
              <p className="ca-recurrence-badge">
                <Repeat size={14} aria-hidden="true" />
                Série {frequencyLabels[event.recurrenceFrequency].toLowerCase()}
              </p>
            ) : null}
            <p className={`ca-status-badge ca-status-badge--${event.status}`}>
              {BOOKING_STATUS_LABELS[event.status]}
            </p>
          </div>
          <button type="button" className="ca-icon-btn" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <div className="ca-detail-highlights">
          <div className="ca-detail-highlight">
            <span className="ca-detail-highlight__label">Quem agendou</span>
            <strong className="ca-detail-highlight__value">{event.bookedByName}</strong>
          </div>
          <div className="ca-detail-highlight">
            <span className="ca-detail-highlight__label">Horário</span>
            <strong className="ca-detail-highlight__value">
              {format(event.originalStart, "dd/MM/yyyy HH:mm")} –{" "}
              {format(event.originalEnd, "HH:mm")}
            </strong>
          </div>
        </div>

        <dl className="ca-detail-list">
          <div>
            <dt>Recurso</dt>
            <dd>{event.resourceName}</dd>
          </div>
          <div>
            <dt>Início</dt>
            <dd>{format(event.originalStart, "dd/MM/yyyy HH:mm")}</dd>
          </div>
          <div>
            <dt>Término</dt>
            <dd>{format(event.originalEnd, "dd/MM/yyyy HH:mm")}</dd>
          </div>
          {event.status === "pending" ? (
            <div>
              <dt>Aprovar até</dt>
              <dd>
                {format(event.originalStart, "dd/MM/yyyy HH:mm")}
                <small className="ca-table__sub"> Início do horário solicitado</small>
              </dd>
            </div>
          ) : null}
          {event.decidedByName ? (
            <div>
              <dt>Decisão</dt>
              <dd>
                {event.decidedByName}
                {event.decisionReason ? ` — ${event.decisionReason}` : ""}
              </dd>
            </div>
          ) : null}
          {event.notes ? (
            <div>
              <dt>Observações</dt>
              <dd>{event.notes}</dd>
            </div>
          ) : null}
        </dl>

        {showCancelOptions ? (
          <div className="ca-cancel-scope">
            <p className="ca-cancel-scope__title">O que deseja cancelar?</p>
            <div
              className="ca-recurrence-options ca-recurrence-options--stack"
              role="radiogroup"
              aria-label="Escopo do cancelamento"
            >
              {CANCEL_SCOPE_CHOICES.map(({ scope, label, hint, icon: Icon }) => {
                const selected = cancelScope === scope;
                return (
                  <label
                    key={scope}
                    className={`ca-recurrence-option${selected ? " ca-recurrence-option--selected" : ""}`}
                  >
                    <input
                      type="radio"
                      className="ca-recurrence-option__input"
                      name="cancelScope"
                      value={scope}
                      checked={selected}
                      onChange={() => setCancelScope(scope)}
                    />
                    <span className="ca-recurrence-option__icon" aria-hidden="true">
                      <Icon size={16} strokeWidth={1.75} />
                    </span>
                    <span className="ca-recurrence-option__text">
                      <span className="ca-recurrence-option__label">{label}</span>
                      <span className="ca-recurrence-option__hint">{hint}</span>
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        ) : null}

        <div className="ca-modal__actions">
          {showCancelOptions ? (
            <button
              type="button"
              className="ca-btn ca-btn--ghost"
              onClick={() => setShowCancelOptions(false)}
            >
              Voltar
            </button>
          ) : (
            <button type="button" className="ca-btn ca-btn--ghost" onClick={onClose}>
              Fechar
            </button>
          )}
          {canCancel ? (
            <button
              type="button"
              className="ca-btn ca-btn--danger"
              disabled={loading}
              onClick={() => void (showCancelOptions ? handleCancel() : openCancelFlow())}
            >
              {loading ? "Cancelando..." : showCancelOptions ? "Confirmar cancelamento" : "Cancelar reserva"}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
