import type { ReactNode } from "react";
import { TriangleAlert } from "lucide-react";

import { ActionButton } from "../actions/ActionButton";

export type ConversationErrorDensity = "comfortable" | "compact";

export type ConversationErrorProps = {
  /** Mensagem principal, já user-safe e resolvida pelo consumidor. */
  title: string;
  /** Detalhe opcional — nunca stack trace, exception repr, tokens,
   *  digests, session ids ou internals de provider. */
  description?: ReactNode;
  /** Ícone decorativo; default alerta genérico do kit (aria-hidden). */
  icon?: ReactNode;
  /** Ação de recuperação opcional — renderizada somente quando
   *  `actionLabel` E `onAction` existem. Nunca retry automático. */
  actionLabel?: string;
  onAction?: () => void;
  actionDisabled?: boolean;
  /** Estado transitório do consumidor — desabilita a ação para impedir
   *  double submit. O componente não cria estado próprio. */
  loading?: boolean;
  density?: ConversationErrorDensity;
  className?: string;
};

/**
 * Superfície inline de falha de interação conversacional — "esta
 * interação não pôde ser concluída; o usuário continua no controle e
 * pode se recuperar". Posicionada no footer do ConversationWorkspace,
 * acima do composer.
 *
 * APENAS apresentação: não conhece Error objects, HTTP status,
 * DeliaInteractionError, sessão, auth, PREPARE/ACT, message_kind ou
 * provider metadata. O consumidor OWNS detecção, copy, draft e a
 * decisão de retry.
 *
 * Distinta de `ConversationStatus` (estado semântico de uma resposta
 * concluída — SOURCE_UNAVAILABLE/AUTHZ_DENIED/WRITE_REJECTED são
 * outcomes, não falha de transporte), de `GovernedConfirmation`
 * (decisão governada) e de `MessageComposer.error` (erro do campo).
 */
export function ConversationError({
  title,
  description,
  icon,
  actionLabel,
  onAction,
  actionDisabled = false,
  loading = false,
  density = "comfortable",
  className,
}: ConversationErrorProps) {
  const rootClass = [
    "delpi-ui-conversation-error",
    density === "compact" ? "delpi-ui-conversation-error--compact" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const showAction = Boolean(actionLabel && onAction);

  return (
    <div className={rootClass} role="alert">
      <span className="delpi-ui-conversation-error__icon" aria-hidden="true">
        {icon ?? <TriangleAlert size={16} strokeWidth={2} />}
      </span>
      <div className="delpi-ui-conversation-error__body">
        <p className="delpi-ui-conversation-error__title">{title}</p>
        {description ? (
          <div className="delpi-ui-conversation-error__description">
            {description}
          </div>
        ) : null}
        {showAction ? (
          <div className="delpi-ui-conversation-error__action">
            <ActionButton
              variant="ghost"
              disabled={actionDisabled || loading}
              onClick={onAction}
            >
              {actionLabel}
            </ActionButton>
          </div>
        ) : null}
      </div>
    </div>
  );
}
