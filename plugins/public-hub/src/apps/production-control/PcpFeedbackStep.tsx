import { useState } from "react";
import { Loader2, PackageSearch } from "lucide-react";
import type {
  MachineLoadOperation,
  PublicOperationMaterial,
} from "./api.ts";
import { usePublicOperationMaterials } from "./usePublicOperationMaterials.ts";
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
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  /** Rascunho mora no fluxo (sheet) — voltar etapa preserva a digitação. */
  note: string;
  selected: ReadonlySet<string>;
  busy: boolean;
  error: string | null;
  onNoteChange: (value: string) => void;
  onToggleMaterial: (code: string) => void;
  /** Envia nota + códigos; o fluxo decide a navegação conforme o resultado. */
  onSubmit: () => void;
  onCancel: () => void;
};

/** Materiais com saldo em aberto primeiro — escolha provável do operador. */
function sortMaterialsByOpenQty(
  items: PublicOperationMaterial[],
): PublicOperationMaterial[] {
  return [...items].sort((a, b) => Number(b.open_qty > 0) - Number(a.open_qty > 0));
}

/**
 * Etapa «Impedimento ao PCP» da central «Pedir ajuda». Mesmo conteúdo do
 * antigo OperatorFeedbackModal — situação/motivo fixos do catálogo C3,
 * seleção obrigatória de materiais reais da OP (lista oficial SD4) e nota
 * opcional — renderizada como etapa do fluxo, sem superfície própria.
 */
export function PcpFeedbackStep({
  token,
  branch,
  operation,
  note,
  selected,
  busy,
  error,
  onNoteChange,
  onToggleMaterial,
  onSubmit,
  onCancel,
}: Props) {
  const [selectionError, setSelectionError] = useState(false);
  const materialsResult = usePublicOperationMaterials(
    token,
    branch,
    operation.production_order,
    operation.operation_code,
    true,
  );
  const materials = sortMaterialsByOpenQty(materialsResult.data?.items ?? []);
  const materialsState = materialsResult.loading
    ? "loading"
    : materialsResult.error
      ? "error"
      : materialsResult.data
        ? "ready"
        : "idle";

  const type = OPERATOR_FEEDBACK_TYPES.find(
    (item) => item.code === DEFAULT_FEEDBACK_TYPE,
  );
  const reason = OPERATOR_FEEDBACK_REASONS.find(
    (item) => item.code === DEFAULT_FEEDBACK_REASON,
  );

  const toggle = (code: string) => {
    setSelectionError(false);
    onToggleMaterial(code);
  };

  const submit = () => {
    if (busy) return;
    if (selected.size === 0) {
      setSelectionError(true);
      return;
    }
    onSubmit();
  };

  return (
    <>
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
          selectionError ? "pcp-help-materials-error" : undefined
        }
      >
        <legend className="pcp-pub__feedback-materials-title">
          <PackageSearch size={16} strokeWidth={2.2} aria-hidden="true" />
          Quais materiais estão impedindo a produção?
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
            id="pcp-help-materials-error"
            className="pcp-pub__run-error"
            role="alert"
          >
            {MATERIAL_SELECTION_REQUIRED}
          </p>
        ) : null}
      </fieldset>

      <label
        className="pcp-pub__feedback-note-label"
        htmlFor="pcp-help-feedback-note"
      >
        Observação <span>(opcional)</span>
      </label>
      <textarea
        id="pcp-help-feedback-note"
        className="pcp-pub__feedback-note"
        value={note}
        onChange={(event) => onNoteChange(event.target.value)}
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
          onClick={submit}
          disabled={
            busy || materialsState === "loading" || materialsState === "error"
          }
          aria-busy={busy}
        >
          {busy ? "Enviando…" : "Enviar aviso ao PCP"}
        </button>
        <button
          type="button"
          className="pcp-pub__btn pcp-pub__btn--ghost"
          onClick={onCancel}
          disabled={busy}
        >
          Cancelar
        </button>
      </div>
    </>
  );
}
