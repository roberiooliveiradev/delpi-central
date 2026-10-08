import { useEffect, useRef, useState } from "react";
import { Wrench } from "lucide-react";
import type { MachineLoadOperation } from "./api.ts";
import {
  PROCESS_ISSUE_DISCLAIMER,
  PROCESS_ISSUE_MATERIAL_CODE_MAX_LENGTH,
  PROCESS_ISSUE_NOTE_MAX_LENGTH,
  PROCESS_ISSUE_REASON_REQUIRED,
  PROCESS_ISSUE_REASONS,
  PROCESS_ISSUE_TOOL_CODE_MAX_LENGTH,
  processIssueReason,
  type ProcessIssueDraft,
} from "./processIssue.ts";
import type { ProcessIssueSubmitResult } from "./useProcessIssue.ts";

type Props = {
  open: boolean;
  operation: MachineLoadOperation;
  workCenter: string;
  busy: boolean;
  error: string | null;
  onSubmit: (draft: ProcessIssueDraft) => Promise<ProcessIssueSubmitResult>;
  onClose: () => void;
};

/**
 * Modal «Informar problema de processo» (P3). Apenas o motivo é obrigatório —
 * ferramenta/material/nota são declarações opcionais do operador, nunca
 * validadas contra SD4/cadastro. Abrir o modal NÃO dispara consultas: todo o
 * enriquecimento (snapshot PUBLISHED + materiais SD4) acontece no backend.
 */
export function ProcessIssueModal({
  open,
  operation,
  workCenter,
  busy,
  error,
  onSubmit,
  onClose,
}: Props) {
  const [issueCode, setIssueCode] = useState<string | null>(null);
  const [toolCode, setToolCode] = useState("");
  const [materialCode, setMaterialCode] = useState("");
  const [note, setNote] = useState("");
  const [reasonError, setReasonError] = useState(false);

  // Refs frescas — o tick do contador re-renderiza a árvore e não pode apagar
  // o que o operador está digitando nem bloquear o Escape durante o envio.
  const busyRef = useRef(busy);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    busyRef.current = busy;
    onCloseRef.current = onClose;
  });

  // Reset na abertura (transição false -> true) — padrão «adjust state
  // during render»: síncrono, sem depender de microtask/effect.
  const [wasOpen, setWasOpen] = useState(open);
  if (open !== wasOpen) {
    setWasOpen(open);
    if (open) {
      setIssueCode(null);
      setToolCode("");
      setMaterialCode("");
      setNote("");
      setReasonError(false);
    }
  }

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busyRef.current) onCloseRef.current();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!open) return null;

  const reason = processIssueReason(issueCode);
  const productLine = operation.product_description || operation.product_code;

  const submit = async () => {
    if (busy) return;
    if (!reason) {
      setReasonError(true);
      return;
    }
    const result = await onSubmit({
      issueCode: reason.code,
      toolCode: toolCode.trim() || null,
      materialCode: materialCode.trim() || null,
      note: note.trim() || null,
    });
    if (result.ok) onClose();
  };

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-process-issue-title"
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
            <Wrench size={22} strokeWidth={2.2} />
          </span>
          <div>
            <h3 id="pcp-process-issue-title" className="pcp-pub__run-title">
              Informar problema de processo
            </h3>
            <p className="pcp-pub-modal__lede">
              OP {operation.production_order} · Operação{" "}
              {operation.operation_code} · {workCenter}
            </p>
            {productLine ? (
              <p className="pcp-pub-modal__lede">{productLine}</p>
            ) : null}
          </div>
        </div>

        <fieldset
          className="pcp-pub__issue-reasons"
          aria-describedby={
            reasonError ? "pcp-process-issue-reason-error" : undefined
          }
        >
          <legend className="pcp-pub__feedback-materials-title">
            O que está acontecendo?
          </legend>
          <div className="pcp-pub__issue-reasons-grid">
            {PROCESS_ISSUE_REASONS.map((item) => (
              <button
                key={item.code}
                type="button"
                className={
                  "pcp-pub__issue-reason" +
                  (issueCode === item.code ? " is-selected" : "")
                }
                aria-pressed={issueCode === item.code}
                disabled={busy}
                onClick={() => {
                  setIssueCode(item.code);
                  setReasonError(false);
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
          {reasonError ? (
            <p
              id="pcp-process-issue-reason-error"
              className="pcp-pub__run-error"
              role="alert"
            >
              {PROCESS_ISSUE_REASON_REQUIRED}
            </p>
          ) : null}
        </fieldset>

        {reason?.auxiliaryField === "toolCode" ? (
          <>
            <label
              className="pcp-pub__feedback-note-label"
              htmlFor="pcp-issue-tool-code"
            >
              {reason.auxiliaryLabel}
            </label>
            <input
              id="pcp-issue-tool-code"
              className="pcp-pub__feedback-note pcp-pub__issue-aux-input"
              type="text"
              value={toolCode}
              onChange={(event) => setToolCode(event.target.value)}
              maxLength={PROCESS_ISSUE_TOOL_CODE_MAX_LENGTH}
              disabled={busy}
              placeholder={reason.auxiliaryPlaceholder ?? ""}
            />
          </>
        ) : null}

        {reason?.auxiliaryField === "materialCode" ? (
          <>
            <label
              className="pcp-pub__feedback-note-label"
              htmlFor="pcp-issue-material-code"
            >
              {reason.auxiliaryLabel}
            </label>
            <input
              id="pcp-issue-material-code"
              className="pcp-pub__feedback-note pcp-pub__issue-aux-input"
              type="text"
              value={materialCode}
              onChange={(event) => setMaterialCode(event.target.value)}
              maxLength={PROCESS_ISSUE_MATERIAL_CODE_MAX_LENGTH}
              disabled={busy}
              placeholder={reason.auxiliaryPlaceholder ?? ""}
            />
          </>
        ) : null}

        <label
          className="pcp-pub__feedback-note-label"
          htmlFor="pcp-process-issue-note"
        >
          Observação <span>(opcional)</span>
        </label>
        <textarea
          id="pcp-process-issue-note"
          className="pcp-pub__feedback-note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={PROCESS_ISSUE_NOTE_MAX_LENGTH}
          rows={3}
          disabled={busy}
          placeholder="Acrescente algum detalhe que possa ajudar Processos."
        />

        <p className="pcp-pub__feedback-disclaimer">
          {PROCESS_ISSUE_DISCLAIMER}
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
            {busy ? "Enviando…" : "Enviar para Processos"}
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
