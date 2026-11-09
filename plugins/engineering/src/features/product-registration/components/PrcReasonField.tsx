import { useState } from "react";
import { MessageSquarePlus, MessageSquareText } from "lucide-react";

import { EngineeringActionButton } from "../../../ui/engineeringUi";

export const PRC_REASON_MAX = 250;

/** D14-FIX — gatilho compacto de justificativa contextual: só aparece
 * junto ao campo efetivamente alterado/preenchido. Ghost oficial do kit
 * (`delpi-ui-action-btn--link`), largura do conteúdo, alinhado ao campo;
 * `MessageSquareText` + contador indicam razão já registrada. */
export function PrcReasonToggle({
  id,
  value,
  open,
  onToggle,
  disabled,
  label = "Justificar",
}: {
  id: string;
  value: string;
  open: boolean;
  onToggle: () => void;
  disabled?: boolean;
  label?: string;
}) {
  const len = value.trim().length;
  return (
    <EngineeringActionButton
      variant="link"
      className="engineering-prc__reason-toggle"
      disabled={disabled}
      aria-expanded={open}
      aria-label={
        len
          ? `Editar justificativa (${len}/${PRC_REASON_MAX} caracteres)`
          : "Adicionar justificativa opcional"
      }
      title="Adicionar justificativa opcional"
      onClick={onToggle}
    >
      {len ? (
        <MessageSquareText size={13} aria-hidden />
      ) : (
        <MessageSquarePlus size={13} aria-hidden />
      )}
      <span id={id}>{len ? "Editar justificativa" : label}</span>
      {len ? (
        <span className="engineering-prc__reason-filled">
          {len}/{PRC_REASON_MAX}
        </span>
      ) : null}
    </EngineeringActionButton>
  );
}

/** D14-FIX — editor contextual (textarea multiline ≤250, contador,
 * Recolher preserva o texto, Remover limpa só esta justificativa).
 * Em tabelas, renderizado na linha auxiliar da `<tr>` (nunca estoura a
 * célula); em formulários, expande inline via `PrcReasonField`. */
export function PrcReasonEditor({
  id,
  value,
  onChange,
  onCollapse,
  disabled,
  label = "Justificativa (opcional)",
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  onCollapse: () => void;
  disabled?: boolean;
  label?: string;
}) {
  const len = value.length;
  return (
    <div className="engineering-prc__reason" id={`${id}-editor`}>
      <label className="engineering-prc__reason-label" htmlFor={`${id}-text`}>
        {label}
      </label>
      <textarea
        id={`${id}-text`}
        className="engineering-prc__reason-input"
        rows={3}
        maxLength={PRC_REASON_MAX}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="engineering-prc__reason-footer">
        <span
          className={
            len >= PRC_REASON_MAX
              ? "engineering-prc__reason-count engineering-prc__reason-count--full"
              : "engineering-prc__reason-count"
          }
          aria-live="polite"
        >
          {len}/{PRC_REASON_MAX} caracteres
        </span>
        <span className="engineering-prc__reason-actions">
          <EngineeringActionButton
            variant="link"
            disabled={disabled}
            onClick={onCollapse}
          >
            Recolher
          </EngineeringActionButton>
          {value ? (
            <EngineeringActionButton
              variant="link"
              disabled={disabled}
              onClick={() => {
                onChange("");
                onCollapse();
              }}
            >
              Remover justificativa
            </EngineeringActionButton>
          ) : null}
        </span>
      </div>
    </div>
  );
}

/** D14 — justificativa individual opcional, colapsada por padrão.
 * Composição inline (campos SB1 do formulário): o editor expande no
 * próprio lugar do gatilho. */
export function PrcReasonField({
  id,
  value,
  onChange,
  disabled,
  label = "Justificar",
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  label?: string;
}) {
  const [open, setOpen] = useState(Boolean(value));

  if (!open) {
    return (
      <PrcReasonToggle
        id={id}
        value={value}
        open={false}
        disabled={disabled}
        label={label}
        onToggle={() => setOpen(true)}
      />
    );
  }
  return (
    <PrcReasonEditor
      id={id}
      value={value}
      onChange={onChange}
      disabled={disabled}
      onCollapse={() => setOpen(false)}
    />
  );
}
