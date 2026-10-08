import { useEffect, useRef, useState } from "react";
import { Loader2, MessageSquareWarning, PackageSearch } from "lucide-react";
import type {
  MachineLoadOperation,
  PublicOperationMaterial,
} from "./api.ts";
import { usePublicOperationMaterials } from "./usePublicOperationMaterials.ts";
import type { FeedbackSubmitResult } from "./useOperatorFeedback.ts";
import {
  DEFAULT_FEEDBACK_REASON,
  DEFAULT_FEEDBACK_TYPE,
  FEEDBACK_NOTE_MAX_LENGTH,
  MATERIALS_LOAD_ERROR,
  MATERIAL_SELECTION_REQUIRED,
  OPERATOR_FEEDBACK_REASONS,
  OPERATOR_FEEDBACK_TYPES,
} from "./operatorFeedback.ts";

type Props = {
  open: boolean;
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  workCenter: string;
  busy: boolean;
  error: string | null;
  onSubmit: (
    note: string | null,
    materialCodes: string[],
  ) => Promise<FeedbackSubmitResult>;
  onClose: () => void;
};

/** Materiais com saldo em aberto primeiro — escolha provável do operador. */
function sortMaterialsByOpenQty(
  items: PublicOperationMaterial[],
): PublicOperationMaterial[] {
  return [...items].sort((a, b) => Number(b.open_qty > 0) - Number(a.open_qty > 0));
}

/**
 * Modal «Informar impedimento ao PCP». Situação e motivo vêm do catálogo da
 * C3; na C5 o motivo missing_material exige selecionar materiais reais da OP
 * (lista oficial SD4) — o envio leva só os códigos, nunca snapshots.
 * Reforço explícito: o aviso não pausa nem encerra a produção.
 */
export function OperatorFeedbackModal({
  open,
  token,
  branch,
  operation,
  workCenter,
  busy,
  error,
  onSubmit,
  onClose,
}: Props) {
  const [note, setNote] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [selectionError, setSelectionError] = useState(false);
  const materialsResult = usePublicOperationMaterials(
    token,
    branch,
    operation.production_order,
    operation.operation_code,
    open,
  );
  const materials = sortMaterialsByOpenQty(materialsResult.data?.items ?? []);
  const materialsState = materialsResult.loading
    ? "loading"
    : materialsResult.error
      ? "error"
      : materialsResult.data
        ? "ready"
        : "idle";

  // Refs frescas para callbacks/props que mudam a cada render do pai —
  // o tick do contador de peças re-renderiza a árvore inteira e NÃO pode
  // apagar o que o operador está digitando no modal.
  const busyRef = useRef(busy);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    busyRef.current = busy;
    onCloseRef.current = onClose;
  });

  // Reset somente na abertura (transição false -> true). Depender de
  // busy/onClose aqui apagaria o formulário a cada re-render do pai.
  useEffect(() => {
    if (!open) return;
    queueMicrotask(() => {
      setNote("");
      setSelected(new Set());
      setSelectionError(false);
    });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busyRef.current) onCloseRef.current();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!open) return null;

  const type = OPERATOR_FEEDBACK_TYPES.find(
    (item) => item.code === DEFAULT_FEEDBACK_TYPE,
  );
  const reason = OPERATOR_FEEDBACK_REASONS.find(
    (item) => item.code === DEFAULT_FEEDBACK_REASON,
  );

  const toggle = (code: string) => {
    setSelectionError(false);
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  };

  const submit = async () => {
    if (busy) return;
    if (selected.size === 0) {
      setSelectionError(true);
      return;
    }
    const result = await onSubmit(note.trim() || null, [...selected]);
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

        <fieldset
          className="pcp-pub__feedback-materials"
          aria-describedby={
            selectionError ? "pcp-feedback-materials-error" : undefined
          }
        >
          <legend className="pcp-pub__feedback-materials-title">
            <PackageSearch size={16} strokeWidth={2.2} aria-hidden="true" />
            Qual material está faltando?
          </legend>

          {materialsState === "loading" ? (
            <p className="pcp-pub__feedback-muted" role="status">
              <Loader2 className="pcp-pub__spin" size={16} aria-hidden="true" />
              Carregando materiais da operação…
            </p>
          ) : null}

          {materialsState === "error" ? (
            <div className="pcp-pub__feedback-materials-error" role="alert">
              <p className="pcp-pub__feedback-muted">{MATERIALS_LOAD_ERROR}</p>
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--ghost"
                onClick={materialsResult.reload}
                disabled={busy}
              >
                Tentar novamente
              </button>
            </div>
          ) : null}

          {materialsState === "ready" && materials.length === 0 ? (
            <p className="pcp-pub__feedback-muted">
              Nenhum material encontrado nesta operação.
            </p>
          ) : null}

          {materialsState === "ready" && materials.length > 0 ? (
            <ul className="pcp-pub__feedback-materials-list">
              {materials.map((material) => {
                const checked = selected.has(material.product_code);
                return (
                  <li key={material.product_code}>
                    <label
                      className={
                        "pcp-pub__feedback-material" +
                        (checked ? " is-selected" : "") +
                        (material.open_qty <= 0 ? " is-empty" : "")
                      }
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled={busy}
                        onChange={() => toggle(material.product_code)}
                      />
                      <span className="pcp-pub__feedback-material-body">
                        <span className="pcp-pub__feedback-material-head">
                          <strong>{material.product_code}</strong>
                          <span className="pcp-pub__feedback-material-qty">
                            Saldo: {material.open_qty} {material.unit}
                          </span>
                        </span>
                        <span className="pcp-pub__feedback-material-desc">
                          {material.description}
                        </span>
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
          ) : null}

          {selectionError ? (
            <p
              id="pcp-feedback-materials-error"
              className="pcp-pub__run-error"
              role="alert"
            >
              {MATERIAL_SELECTION_REQUIRED}
            </p>
          ) : null}
        </fieldset>

        <label className="pcp-pub__feedback-note-label" htmlFor="pcp-feedback-note">
          Observação <span>(opcional)</span>
        </label>
        <textarea
          id="pcp-feedback-note"
          className="pcp-pub__feedback-note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={FEEDBACK_NOTE_MAX_LENGTH}
          rows={3}
          disabled={busy}
          placeholder="Acrescente algum detalhe, se necessário."
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
            disabled={busy || materialsState === "loading" || materialsState === "error"}
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
