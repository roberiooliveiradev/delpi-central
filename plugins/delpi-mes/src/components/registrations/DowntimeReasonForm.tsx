import { useId, useState, type FormEvent } from "react";

import type { CreateDowntimeReasonInput, DowntimeReason, UpdateDowntimeReasonInput } from "../../api/downtimeReasonsApi";

export type DowntimeReasonFormMode = "create" | "edit";

export type DowntimeReasonFormProps = {
  mode: DowntimeReasonFormMode;
  reason?: DowntimeReason;
  busy: boolean;
  error: string | null;
  categorySuggestions: string[];
  onSubmit: (values: CreateDowntimeReasonInput | UpdateDowntimeReasonInput) => void;
  onCancel: () => void;
};

const CODE_PATTERN = /^[a-z0-9_]{1,40}$/;
const LABEL_MAX = 120;
const CATEGORY_MAX = 60;

export function DowntimeReasonForm({
  mode,
  reason,
  busy,
  error,
  categorySuggestions,
  onSubmit,
  onCancel,
}: DowntimeReasonFormProps) {
  const id = useId();
  const [code, setCode] = useState(reason?.code ?? "");
  const [label, setLabel] = useState(reason?.label ?? "");
  const [category, setCategory] = useState(reason?.category ?? "");
  const [requiresNote, setRequiresNote] = useState(reason?.requiresNote ?? false);
  const [sortOrder, setSortOrder] = useState(String(reason?.sortOrder ?? 0));
  const [localError, setLocalError] = useState<string | null>(null);
  const shownError = error ?? localError;
  const categoryListId = `${id}-categories`;

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (busy) return;
    const normalizedCode = code.trim().toLowerCase();
    const normalizedLabel = label.trim();
    const normalizedCategory = category.trim().toLowerCase();
    const order = Number(sortOrder);

    if (mode === "create" && !CODE_PATTERN.test(normalizedCode)) {
      setLocalError("Informe um código válido: letras minúsculas, números e underscore (máx. 40).");
      return;
    }
    if (!normalizedLabel || normalizedLabel.length > LABEL_MAX) {
      setLocalError(`Informe uma descrição de até ${LABEL_MAX} caracteres.`);
      return;
    }
    if (!normalizedCategory || normalizedCategory.length > CATEGORY_MAX) {
      setLocalError(`Informe uma categoria de até ${CATEGORY_MAX} caracteres.`);
      return;
    }
    if (!Number.isInteger(order) || order < 0) {
      setLocalError("A ordem de exibição deve ser um inteiro maior ou igual a zero.");
      return;
    }

    setLocalError(null);
    if (mode === "create") {
      onSubmit({ code: normalizedCode, label: normalizedLabel, category: normalizedCategory, requiresNote, sortOrder: order });
    } else {
      onSubmit({ label: normalizedLabel, category: normalizedCategory, requiresNote, sortOrder: order });
    }
  };

  return (
    <form className="delpi-mes-form" onSubmit={handleSubmit} noValidate>
      <div className="delpi-mes-field">
        <label htmlFor={`${id}-code`}>Código</label>
        <input
          id={`${id}-code`}
          value={code}
          onChange={(event) => setCode(event.target.value.toLowerCase())}
          maxLength={40}
          disabled={busy}
          readOnly={mode === "edit"}
          aria-readonly={mode === "edit"}
          autoComplete="off"
          placeholder="falta_embalagem"
          required
        />
        <p className="delpi-mes-field__help">
          {mode === "edit"
            ? "Identificador técnico estável. Não pode ser alterado após a criação."
            : "Identificador técnico estável. Use letras minúsculas, números e underscore. Ex.: falta_embalagem"}
        </p>
      </div>
      <div className="delpi-mes-field">
        <label htmlFor={`${id}-label`}>Descrição</label>
        <input
          id={`${id}-label`}
          value={label}
          onChange={(event) => setLabel(event.target.value)}
          maxLength={LABEL_MAX}
          disabled={busy}
          required
        />
      </div>
      <div className="delpi-mes-field">
        <label htmlFor={`${id}-category`}>Categoria</label>
        <input
          id={`${id}-category`}
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          maxLength={CATEGORY_MAX}
          disabled={busy}
          list={categoryListId}
          autoComplete="off"
          placeholder="machine"
          required
        />
        <datalist id={categoryListId}>
          {categorySuggestions.map((suggestion) => (
            <option key={suggestion} value={suggestion} />
          ))}
        </datalist>
        <p className="delpi-mes-field__help">Texto livre; as sugestões refletem as categorias já utilizadas.</p>
      </div>
      <div className="delpi-mes-field delpi-mes-field--inline">
        <label className="delpi-mes-checkbox" htmlFor={`${id}-requires-note`}>
          <input
            id={`${id}-requires-note`}
            type="checkbox"
            checked={requiresNote}
            onChange={(event) => setRequiresNote(event.target.checked)}
            disabled={busy}
          />
          <span>
            <strong>Exige observação</strong>
            <span className="delpi-mes-field__help">
              Quando ativo, o operador precisa informar uma observação ao utilizar este motivo.
            </span>
          </span>
        </label>
      </div>
      <div className="delpi-mes-field">
        <label htmlFor={`${id}-sort-order`}>Ordem de exibição</label>
        <input
          id={`${id}-sort-order`}
          type="number"
          min={0}
          step={1}
          inputMode="numeric"
          value={sortOrder}
          onChange={(event) => setSortOrder(event.target.value)}
          disabled={busy}
          required
        />
        <p className="delpi-mes-field__help">Define a posição do motivo nas listas de classificação.</p>
      </div>
      {shownError ? (
        <p className="delpi-mes-form__error" role="alert">{shownError}</p>
      ) : null}
      <div className="delpi-mes-form__actions">
        <button type="button" className="delpi-mes-ghost-btn" onClick={onCancel} disabled={busy}>
          Cancelar
        </button>
        <button type="submit" className="delpi-mes-primary-btn" disabled={busy}>
          {busy ? "Salvando…" : mode === "edit" ? "Salvar alterações" : "Criar motivo"}
        </button>
      </div>
    </form>
  );
}
