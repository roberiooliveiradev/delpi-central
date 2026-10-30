import type { MouseEventHandler, ReactNode } from "react";

import { isSafeNavigationHref } from "../layout/PagePath";
import { shouldHandleInlineNavClick } from "../navigation/InlineNavLink";

export type ActionButtonVariant = "default" | "primary" | "ghost" | "link";

type ActionButtonBaseProps = {
  children: ReactNode;
  variant?: ActionButtonVariant;
  disabled?: boolean;
  /**
   * Quando `disabled`, renderiza `aria-disabled` + guarda de clique em vez
   * do atributo nativo — o botão permanece focável e o foco não é perdido
   * para `<body>` quando a ação desabilita o controle no meio do loading.
   * Opt-in: controles de refresh/ação; `type="submit"` continua nativo.
   */
  softDisabled?: boolean;
  className?: string;
  "aria-label"?: string;
  "aria-describedby"?: string;
  "aria-expanded"?: boolean;
  /** Tooltip nativo (obrigatório com `href` para indicar o destino). */
  title?: string;
};

export type ActionButtonProps = ActionButtonBaseProps &
  (
    | {
        href: string;
        title: string;
        type?: undefined;
        onClick?: MouseEventHandler<HTMLAnchorElement>;
      }
    | {
        href?: undefined;
        type?: "button" | "submit";
        onClick?: () => void;
        /** Associa o botão a um `<form id>` fora da árvore do botão (ex.: footer de card). */
        form?: string;
      }
  );

/**
 * Botão de ação canônico dos MFEs (primário, padrão, ghost e link inline).
 * Com `href`, renderiza `<a>` real (SPA same-tab + middle-click nativo).
 *
 * CSS: `styles/action-controls.css` (`.delpi-ui-action-btn*`).
 */
export function ActionButton(props: ActionButtonProps) {
  const {
    children,
    variant = "default",
    disabled = false,
    softDisabled = false,
    className,
    "aria-label": ariaLabel,
    "aria-describedby": ariaDescribedby,
    "aria-expanded": ariaExpanded,
    title,
  } = props;

  const rootClass = [
    "delpi-ui-action-btn",
    variant !== "default" ? `delpi-ui-action-btn--${variant}` : null,
    disabled ? "delpi-ui-action-btn--disabled" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if ("href" in props && props.href) {
    const safeHref = isSafeNavigationHref(props.href) ? props.href.trim() : "#";
    const resolvedTitle = props.title.trim();
    return (
      <a
        className={rootClass}
        href={disabled ? undefined : safeHref}
        title={resolvedTitle}
        aria-label={ariaLabel ?? resolvedTitle}
        aria-describedby={ariaDescribedby}
        aria-expanded={ariaExpanded}
        aria-disabled={disabled || undefined}
        tabIndex={disabled ? -1 : undefined}
        onClick={(event) => {
          if (disabled) {
            event.preventDefault();
            return;
          }
          if (!shouldHandleInlineNavClick(event)) {
            return;
          }
          if (!props.onClick) {
            return;
          }
          event.preventDefault();
          props.onClick(event);
        }}
      >
        {children}
      </a>
    );
  }

  const buttonProps = props as Extract<ActionButtonProps, { href?: undefined }>;
  const soft = disabled && softDisabled && (buttonProps.type ?? "button") !== "submit";

  return (
    <button
      type={buttonProps.type ?? "button"}
      className={rootClass}
      disabled={disabled && !soft}
      aria-disabled={soft || undefined}
      onClick={soft ? undefined : buttonProps.onClick}
      form={buttonProps.form}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedby}
      aria-expanded={ariaExpanded}
      title={title}
    >
      {children}
    </button>
  );
}
