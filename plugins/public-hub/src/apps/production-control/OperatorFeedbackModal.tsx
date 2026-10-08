import { useEffect, useState } from "react";
import { MessageSquareWarning } from "lucide-react";
import type { MachineLoadOperation } from "./api.ts";
import type { FeedbackSubmitResult } from "./useOperatorFeedback.ts";
import {
  DEFAULT_FEEDBACK_REASON,
  DEFAULT_FEEDBACK_TYPE,
  FEEDBACK_NOTE_MAX_LENGTH,
  OPERATOR_FEEDBACK_REASONS,
  OPERATOR_FEEDBACK_TYPES,
} from "./operatorFeedback.ts";

type Props = {
  open: boolean;
  operation: MachineLoadOperation;
  workCenter: string;
  busy: boolean;
  error: string | null;
  onSubmit: (note: string | null) => Promise<FeedbackSubmitResult>;
  onClose: () => void;
};

/**
 * Modal «Informar impedimento ao PCP». Situação e motivo vêm do catálogo da
 * C3 (hoje uma opção de cada); o operador só acrescenta a observação.
 * Reforço explícito: o aviso não pausa nem encerra a produção.
 */
export function OperatorFeedbackModal({
  open,
  operation,
  workCenter,
  busy,
  error,
  onSubmit,
  onClose,
}: Props) {
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!open) return;
    queueMicrotask(() => setNote(""));
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  if (!open) return null;

  const type = OPERATOR_FEEDBACK_TYPES.find(
    (item) => item.code === DEFAULT_FEEDBACK_TYPE,
  );
  const reason = OPERATOR_FEEDBACK_REASONS.find(
    (item) => item.code === DEFAULT_FEEDBACK_REASON,
  );

  const submit = async () => {
    if (busy) return;
    const result = await onSubmit(note.trim() || null);
    if (result.ok) onClose();
  };

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-feedback-title"
    >
      <button
        type="button"
        className="pcp-pub-modal__backdrop"
        aria-label="Fechar"
        onClick={() => {
          if (!busy) onClose();
        }}
      />
      <div className="pcp-pub-modal__panel pcp-pub-modal__panel--feedback">
        <div className="pcp-pub__feedback-modal-head">
          <span className="pcp-pub__feedback-modal-icon" aria-hidden="true">
            <MessageSquareWarning size={22} strokeWidth={2.2} />
          </span>
          <div>
            <h3 id="pcp-feedback-title" className="pcp-pub__run-title">
              Informar impedimento ao PCP
            </h3>
            <p className="pcp-pub-modal__lede">
              OP {operation.production_order} · Operação{" "}
              {operation.operation_code} · {workCenter}
            </p>
          </div>
        </div>

        <dl className="pcp-pub__feedback-fields">
          <div className="pcp-pub__feedback-field">
            <dt>Situação</dt>
            <dd>{type?.label ?? "Impedimento"}</dd>
          </div>
          <div className="pcp-pub__feedback-field">
            <dt>Motivo</dt>
            <dd>{reason?.label ?? "—"}</dd>
          </div>
        </dl>

        <label className="pcp-pub__feedback-note-label" htmlFor="pcp-feedback-note">
          Observação <span>(opcional)</span>
        </label>
        <textarea
          id="pcp-feedback-note"
          className="pcp-pub__feedback-note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={FEEDBACK_NOTE_MAX_LENGTH}
          rows={4}
          disabled={busy}
          placeholder="Se necessário, informe qual material está faltando ou acrescente algum detalhe."
        />

        <p className="pcp-pub__feedback-disclaimer">
          Este aviso informa o PCP, mas não pausa nem encerra a produção.
        </p>

        {error ? (
          <p className="pcp-pub__run-error" role="alert" aria-live="assertive">
            {error}
          </p>
        ) : null}

        <div className="pcp-pub__run-actions">
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--primary"
            onClick={() => void submit()}
            disabled={busy}
            aria-busy={busy}
          >
            {busy ? "Enviando…" : "Enviar aviso ao PCP"}
          </button>
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--ghost"
            onClick={onClose}
            disabled={busy}
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
