import { useEffect, useState } from "react";
import { addHours, format } from "date-fns";

import type { SchedulingResource } from "../api/schedulingApi";
import type { BranchCode } from "../constants/scheduling";

type Props = {
  open: boolean;
  branch: BranchCode;
  resources: SchedulingResource[];
  defaultResourceId?: string;
  defaultStart?: Date;
  defaultEnd?: Date;
  loading?: boolean;
  onClose: () => void;
  onSubmit: (payload: {
    resource_id: string;
    title: string;
    notes?: string;
    start_at: string;
    end_at: string;
  }) => Promise<void>;
};

function toLocalInputValue(date: Date): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function endOneHourAfterStart(startValue: string): string {
  if (!startValue) return "";
  const start = new Date(startValue);
  if (Number.isNaN(start.getTime())) return "";
  return toLocalInputValue(addHours(start, 1));
}

export function BookingModal({
  open,
  branch,
  resources,
  defaultResourceId,
  defaultStart,
  defaultEnd,
  loading = false,
  onClose,
  onSubmit,
}: Props) {
  const [resourceId, setResourceId] = useState(defaultResourceId ?? "");
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [startValue, setStartValue] = useState("");
  const [endValue, setEndValue] = useState("");
  const [endTouched, setEndTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setResourceId(defaultResourceId ?? resources[0]?.id ?? "");
    setTitle("");
    setNotes("");
    setEndTouched(false);
    const initialStart = defaultStart ? toLocalInputValue(defaultStart) : "";
    setStartValue(initialStart);
    if (defaultEnd) {
      setEndValue(toLocalInputValue(defaultEnd));
    } else if (initialStart) {
      setEndValue(endOneHourAfterStart(initialStart));
    } else {
      setEndValue("");
    }
    setError(null);
  }, [open, defaultResourceId, defaultStart, defaultEnd, resources]);

  function handleStartChange(value: string) {
    setStartValue(value);
    if (!value) {
      if (!endTouched) setEndValue("");
      return;
    }

    if (!endTouched) {
      setEndValue(endOneHourAfterStart(value));
      return;
    }

    const start = new Date(value);
    const end = new Date(endValue);
    if (!Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime()) && end <= start) {
      setEndValue(endOneHourAfterStart(value));
    }
  }

  function handleEndChange(value: string) {
    setEndTouched(true);
    setEndValue(value);
  }

  if (!open) return null;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (!resourceId || !title.trim() || !startValue || !endValue) {
      setError("Preencha recurso, título e horários.");
      return;
    }

    const start = new Date(startValue);
    const end = new Date(endValue);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      setError("Horários inválidos.");
      return;
    }
    if (end <= start) {
      setError("O término deve ser posterior ao início.");
      return;
    }

    try {
      await onSubmit({
        resource_id: resourceId,
        title: title.trim(),
        notes: notes.trim() || undefined,
        start_at: start.toISOString(),
        end_at: end.toISOString(),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao reservar.");
    }
  }

  return (
    <div className="ca-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="ca-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ca-booking-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="ca-modal__header">
          <div>
            <p className="ca-modal__eyebrow">Nova reserva · {branch}</p>
            <h2 id="ca-booking-title">Agendar recurso</h2>
          </div>
          <button type="button" className="ca-icon-btn" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <form className="ca-form" onSubmit={(event) => void handleSubmit(event)}>
          <label className="ca-field">
            <span>Recurso</span>
            <select
              value={resourceId}
              onChange={(event) => setResourceId(event.target.value)}
              required
            >
              <option value="">Selecione...</option>
              {resources.map((resource) => (
                <option key={resource.id} value={resource.id}>
                  {resource.name}
                </option>
              ))}
            </select>
          </label>

          <label className="ca-field">
            <span>Título</span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Ex.: Reunião com fornecedor"
              required
            />
          </label>

          <div className="ca-form-row">
            <label className="ca-field">
              <span>Início</span>
              <input
                type="datetime-local"
                value={startValue}
                onChange={(event) => handleStartChange(event.target.value)}
                required
              />
            </label>
            <label className="ca-field">
              <span>Término</span>
              <input
                type="datetime-local"
                value={endValue}
                onChange={(event) => handleEndChange(event.target.value)}
                required
              />
            </label>
          </div>

          <label className="ca-field">
            <span>Observações</span>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
              placeholder="Informações adicionais (opcional)"
            />
          </label>

          {defaultStart && defaultEnd ? (
            <p className="ca-muted">
              Período selecionado: {format(defaultStart, "dd/MM/yyyy HH:mm")} —{" "}
              {format(defaultEnd, "HH:mm")}
            </p>
          ) : null}

          {error ? <p className="ca-alert ca-alert--error">{error}</p> : null}

          <div className="ca-modal__actions">
            <button type="button" className="ca-btn ca-btn--ghost" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="ca-btn ca-btn--primary" disabled={loading}>
              {loading ? "Reservando..." : "Confirmar reserva"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
