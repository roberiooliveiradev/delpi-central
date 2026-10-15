import type { ReactNode } from "react";

import { ActionButton } from "../actions/ActionButton";

export type GovernedConfirmationDensity = "comfortable" | "compact";
export type GovernedConfirmationTone = "neutral" | "warning" | "danger";

export type GovernedConfirmationProps = {
  /** Título resolvido pelo consumidor. */
  title?: string;
  /** Contexto opcional — nunca digests, fingerprints, IDs ou payloads. */
  description?: ReactNode;
  /** Slot opcional de preview disclosure-safe; não renderizar sem dado
   *  legítimo. */
  preview?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmDisabled?: boolean;
  cancelDisabled?: boolean;
  /** Estado transitório do consumidor — desabilita ambas as ações para
   *  impedir double submit. O componente não cria estado próprio. */
  loading?: boolean;
  density?: GovernedConfirmationDensity;
  /** Tonalidade do título/ícone visual; `danger` só com sinal explícito
   *  do consumidor — nunca inferido de texto. */
  tone?: GovernedConfirmationTone;
  className?: string;
  "aria-label"?: string;
};

/**
 * Superfície inline de decisão governada em uma mensagem conversacional.
 *
 * APENAS apresentação: agrupa título/descrição/preview opcional e a
 * linha de ações Confirmar/Cancelar (ActionButton). Não conhece
 * confirmation_request, digests, auth, RBAC, PREPARE/ACT, backend ou
 * regras de negócio — o consumidor decide quando a superfície existe e
 * o que os callbacks fazem. Um clique é intenção do usuário, nunca
 * autorização nem resultado.
 *
 * Distinta de `ConversationStatus` (estado semântico, acima) e de
 * `MessageActionBar` (ações secundárias da mensagem).
 */
export function GovernedConfirmation({
  title = "Confirmação necessária",
  description,
  preview,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  onConfirm,
  onCancel,
  confirmDisabled = false,
  cancelDisabled = false,
  loading = false,
  density = "comfortable",
  tone = "neutral",
  className,
  "aria-label": ariaLabel,
}: GovernedConfirmationProps) {
  const rootClass = [
    "delpi-ui-governed-confirmation",
    tone !== "neutral" ? `delpi-ui-governed-confirmation--${tone}` : null,
    density === "compact"
      ? "delpi-ui-governed-confirmation--compact"
      : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      role="group"
      aria-label={ariaLabel ?? title}
    >
      <p className="delpi-ui-governed-confirmation__title">{title}</p>
      {description ? (
        <div className="delpi-ui-governed-confirmation__description">
          {description}
        </div>
      ) : null}
      {preview ? (
        <div className="delpi-ui-governed-confirmation__preview">
          {preview}
        </div>
      ) : null}
      <div className="delpi-ui-governed-confirmation__actions">
        <ActionButton
          variant="ghost"
          disabled={cancelDisabled || loading}
          onClick={onCancel}
        >
          {cancelLabel}
        </ActionButton>
        <ActionButton
          variant="primary"
          disabled={confirmDisabled || loading}
          onClick={onConfirm}
        >
          {confirmLabel}
        </ActionButton>
      </div>
    </div>
  );
}
