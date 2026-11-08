import { useState } from "react";

/** D14-B — justificativa individual opcional, colapsada por padrão.
 * Textarea multiline, maxLength 250, contador acessível; recolher
 * preserva o texto; remover limpa só esta justificativa. */
export function PrcReasonField({
  id,
  value,
  onChange,
  disabled,
  label = "Adicionar justificativa (opcional)",
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  label?: string;
}) {
  const [open, setOpen] = useState(Boolean(value));
  const len = value.length;

  if (!open) {
    return (
      <button
        type="button"
        id={id}
        className="engineering-prc__reason-toggle"
        disabled={disabled}
        aria-expanded="false"
        onClick={() => setOpen(true)}
      >
        {value ? `Justificativa informada (${len}/250)` : label}
      </button>
    );
  }
  return (
    <div className="engineering-prc__reason">
      <label className="engineering-prc__reason-label" htmlFor={`${id}-text`}>
        Justificativa (opcional)
      </label>
      <textarea
        id={`${id}-text`}
        className="engineering-prc__reason-input"
        rows={3}
        maxLength={250}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="engineering-prc__reason-footer">
        <span
          className={
            len >= 250
              ? "engineering-prc__reason-count engineering-prc__reason-count--full"
              : "engineering-prc__reason-count"
          }
          aria-live="polite"
        >
          {len}/250 caracteres
        </span>
        <span className="engineering-prc__reason-actions">
          <button
            type="button"
            className="engineering-prc__lookup-clear"
            onClick={() => setOpen(false)}
          >
            Recolher
          </button>
          {value ? (
            <button
              type="button"
              className="engineering-prc__lookup-clear"
              onClick={() => onChange("")}
            >
              Remover justificativa
            </button>
          ) : null}
        </span>
      </div>
    </div>
  );
}
