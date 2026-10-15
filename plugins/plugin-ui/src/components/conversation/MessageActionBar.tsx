import type { ReactNode } from "react";

export type MessageActionBarVisibility = "hover-focus" | "always";
export type MessageActionBarDensity = "comfortable" | "compact";
export type MessageActionBarAlign = "start" | "end";

export type MessageActionBarProps = {
  children: ReactNode;
  className?: string;
  /**
   * `hover-focus` (default): ações subordinadas — visíveis quando o
   * ancestral `.delpi-ui-message-action-scope` recebe hover/focus-within
   * ou quando o próprio grupo contém foco; sempre visíveis em pointers
   * sem hover (touch). `always`: sempre visíveis.
   */
  visibility?: MessageActionBarVisibility;
  density?: MessageActionBarDensity;
  align?: MessageActionBarAlign;
  /** Nome acessível do grupo (role="group"). Omitir se redundante. */
  "aria-label"?: string;
};

/**
 * Barra de ações secundárias de uma mensagem conversacional.
 *
 * Apresentação pura: organiza e revela botões (ex.: `IconButton`) de
 * forma subordinada à mensagem. Não conhece clipboard, conteúdo, auth,
 * provenance ou DÉLIA — o consumidor decide quais ações existem e o que
 * executam. Não usar para decisões governadas (confirmação/cancelamento
 * têm superfície própria).
 *
 * Contrato de reveal: colocar `delpi-ui-message-action-scope` no
 * elemento raiz da mensagem que hospeda a barra.
 */
export function MessageActionBar({
  children,
  className,
  visibility = "hover-focus",
  density = "comfortable",
  align = "end",
  "aria-label": ariaLabel,
}: MessageActionBarProps) {
  const rootClass = [
    "delpi-ui-message-action-bar",
    `delpi-ui-message-action-bar--${visibility}`,
    density === "compact" ? "delpi-ui-message-action-bar--compact" : null,
    align === "start" ? "delpi-ui-message-action-bar--start" : null,
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
      {children}
    </div>
  );
}
