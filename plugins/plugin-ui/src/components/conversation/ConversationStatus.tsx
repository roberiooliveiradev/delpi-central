import type { ReactNode } from "react";

import {
  StatusBadge,
  statusBadgeBemClasses,
  type StatusBadgeVariant,
} from "../feedback/StatusBadge";

export type ConversationStatusTone = StatusBadgeVariant;
export type ConversationStatusDensity = "comfortable" | "compact";

export type ConversationStatusProps = {
  /** Texto já resolvido pelo consumidor — o componente nunca
   *  infere estado a partir de conteúdo. */
  label: string;
  tone?: ConversationStatusTone;
  /** Ícone decorativo (renderizado aria-hidden — o label já comunica). */
  icon?: ReactNode;
  /** Complemento opcional inline, também resolvido pelo consumidor. */
  description?: ReactNode;
  density?: ConversationStatusDensity;
  className?: string;
  /** Nome acessível do grupo (role="group"). Omitir se redundante. */
  "aria-label"?: string;
};

const statusBadgeClassNames = statusBadgeBemClasses("delpi-ui");

/**
 * Estado semântico inline de uma mensagem conversacional: ícone
 * decorativo + `StatusBadge` canônico. Apresentação pura — não conhece
 * enums de produto, `message_kind`, auth, permissão ou backend. O
 * consumidor decide SE o estado existe e COMO se chama; o kit só
 * renderiza o chrome subordinado.
 *
 * Não é banner de erro, não é ação governada e não é live region —
 * estados semânticos são conteúdo estático da mensagem.
 */
export function ConversationStatus({
  label,
  tone = "neutral",
  icon,
  description,
  density = "comfortable",
  className,
  "aria-label": ariaLabel,
}: ConversationStatusProps) {
  const rootClass = [
    "delpi-ui-conversation-status",
    `delpi-ui-conversation-status--${tone}`,
    density === "compact" ? "delpi-ui-conversation-status--compact" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      role={ariaLabel ? "group" : undefined}
      aria-label={ariaLabel}
    >
      {icon ? (
        <span className="delpi-ui-conversation-status__icon" aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <StatusBadge
        label={label}
        variant={tone}
        classNames={statusBadgeClassNames}
      />
      {description ? (
        <span className="delpi-ui-conversation-status__description">
          {description}
        </span>
      ) : null}
    </div>
  );
}
