import type { ButtonHTMLAttributes, ReactNode } from "react";

export type IconButtonTone = "default" | "danger" | "primary";

export type IconButtonProps = {
  children: ReactNode;
  "aria-label": string;
  "aria-expanded"?: boolean;
  "aria-haspopup"?: ButtonHTMLAttributes<HTMLButtonElement>["aria-haspopup"];
  "aria-pressed"?: boolean;
  /** Visual selected/pressed state (pairs with aria-pressed when boolean). */
  pressed?: boolean;
  tone?: IconButtonTone;
  type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  /** Focus the control when it mounts (e.g. entering a capture state). */
  autoFocus?: boolean;
};

/**
 * Botão só com ícone (remover item, fechar, etc.).
 *
 * CSS: `styles/action-controls.css` (`.delpi-ui-icon-btn*`).
 */
export function IconButton({
  children,
  "aria-label": ariaLabel,
  "aria-expanded": ariaExpanded,
  "aria-haspopup": ariaHaspopup,
  "aria-pressed": ariaPressed,
  pressed,
  tone = "default",
  type = "button",
  disabled = false,
  onClick,
  className,
  autoFocus = false,
}: IconButtonProps) {
  const isPressed = pressed ?? ariaPressed;
  const rootClass = [
    "delpi-ui-icon-btn",
    tone !== "default" ? `delpi-ui-icon-btn--${tone}` : null,
    isPressed ? "delpi-ui-icon-btn--pressed" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      type={type}
      className={rootClass}
      disabled={disabled}
      onClick={onClick}
      aria-label={ariaLabel}
      aria-expanded={ariaExpanded}
      aria-haspopup={ariaHaspopup}
      aria-pressed={typeof isPressed === "boolean" ? isPressed : undefined}
      autoFocus={autoFocus}
    >
      {children}
    </button>
  );
}
