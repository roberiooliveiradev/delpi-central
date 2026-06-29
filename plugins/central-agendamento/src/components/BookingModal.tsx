import { useEffect, useState } from "react";
import { addHours, addMonths, addWeeks, format } from "date-fns";
import { Calendar, CalendarDays, CalendarRange } from "lucide-react";

import type { RecurrenceFrequency, RecurrencePayload, SchedulingResource } from "../api/schedulingApi";
import type { BranchCode } from "../constants/scheduling";

type RecurrenceMode = "none" | RecurrenceFrequency;

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
    recurrence?: RecurrencePayload;
  }) => Promise<void>;
};

function toLocalInputValue(date: Date): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function toLocalDateValue(date: Date): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function endOneHourAfterStart(startValue: string): string {
  if (!startValue) return "";
  const start = new Date(startValue);
  if (Number.isNaN(start.getTime())) return "";
  return toLocalInputValue(addHours(start, 1));
}

function defaultUntilDate(startValue: string, mode: RecurrenceMode): string {
  if (!startValue) return "";
  const start = new Date(startValue);
  if (Number.isNaN(start.getTime())) return "";
  const until = mode === "monthly" ? addMonths(start, 6) : addWeeks(start, 8);
  return toLocalDateValue(until);
}

const RECURRENCE_LABELS: Record<RecurrenceFrequency, string> = {
  weekly: "Semanal",
  monthly: "Mensal",
};

const RECURRENCE_CHOICES: Array<{
  mode: RecurrenceMode;
  label: string;
  hint: string;
  icon: typeof Calendar;
}> = [
  { mode: "none", label: "Não repetir", hint: "Reserva única", icon: Calendar },
  { mode: "weekly", label: "Semanal", hint: "Mesmo dia da semana", icon: CalendarDays },
  { mode: "monthly", label: "Mensal", hint: "Mesmo dia do mês", icon: CalendarRange },
];

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
  const [recurrenceMode, setRecurrenceMode] = useState<RecurrenceMode>("none");
  const [untilDate, setUntilDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setResourceId(defaultResourceId ?? resources[0]?.id ?? "");
    setTitle("");
    setNotes("");
    setEndTouched(false);
    setRecurrenceMode("none");
    const initialStart = defaultStart ? toLocalInputValue(defaultStart) : "";
    setStartValue(initialStart);
    if (defaultEnd) {
      setEndValue(toLocalInputValue(defaultEnd));
    } else if (initialStart) {
      setEndValue(endOneHourAfterStart(initialStart));
    } else {
      setEndValue("");
    }
    setUntilDate(initialStart ? defaultUntilDate(initialStart, "weekly") : "");
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
    } else {
      const start = new Date(value);
      const end = new Date(endValue);
      if (!Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime()) && end <= start) {
        setEndValue(endOneHourAfterStart(value));
      }
    }

    if (recurrenceMode !== "none") {
      setUntilDate(defaultUntilDate(value, recurrenceMode));
    }
  }

  function handleRecurrenceModeChange(mode: RecurrenceMode) {
    setRecurrenceMode(mode);
    if (mode !== "none" && startValue) {
      setUntilDate(defaultUntilDate(startValue, mode));
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

    let recurrence: RecurrencePayload | undefined;
    if (recurrenceMode !== "none") {
      if (!untilDate) {
        setError("Informe até quando a reserva deve se repetir.");
        return;
      }
      const until = new Date(`${untilDate}T23:59:59`);
      if (Number.isNaN(until.getTime())) {
        setError("Data final da recorrência inválida.");
        return;
      }
      if (until < start) {
        setError("A data final da recorrência deve ser igual ou posterior ao início.");
        return;
      }
      recurrence = {
        frequency: recurrenceMode,
        until: until.toISOString(),
      };
    }

    try {
      await onSubmit({
        resource_id: resourceId,
        title: title.trim(),
        notes: notes.trim() || undefined,
        start_at: start.toISOString(),
        end_at: end.toISOString(),
        recurrence,
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

          <fieldset className="ca-fieldset">
            <legend>Repetir</legend>
            <div className="ca-recurrence-options" role="radiogroup" aria-label="Repetição">
              {RECURRENCE_CHOICES.map(({ mode, label, hint, icon: Icon }) => {
                const selected = recurrenceMode === mode;
                return (
                  <label
                    key={mode}
                    className={`ca-recurrence-option${selected ? " ca-recurrence-option--selected" : ""}`}
                  >
                    <input
                      type="radio"
                      className="ca-recurrence-option__input"
                      name="recurrence"
                      value={mode}
                      checked={selected}
                      onChange={() => handleRecurrenceModeChange(mode)}
                    />
                    <span className="ca-recurrence-option__icon" aria-hidden="true">
                      <Icon size={18} strokeWidth={1.75} />
                    </span>
                    <span className="ca-recurrence-option__text">
                      <span className="ca-recurrence-option__label">{label}</span>
                      <span className="ca-recurrence-option__hint">{hint}</span>
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          {recurrenceMode !== "none" ? (
            <label className="ca-field">
              <span>Repetir até</span>
              <input
                type="date"
                value={untilDate}
                onChange={(event) => setUntilDate(event.target.value)}
                required
              />
              <p className="ca-muted ca-field-hint">
                A reserva será criada {RECURRENCE_LABELS[recurrenceMode].toLowerCase()} no mesmo
                horário até a data informada.
              </p>
            </label>
          ) : null}

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
              {loading
                ? "Reservando..."
                : recurrenceMode === "none"
                  ? "Confirmar reserva"
                  : "Confirmar série recorrente"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
