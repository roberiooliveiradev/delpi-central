import type { ReactNode } from "react";

export type ActionButtonVariant = "default" | "primary" | "ghost" | "link";

export type ActionButtonProps = {
  children: ReactNode;
  variant?: ActionButtonVariant;
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  "aria-label"?: string;
};

/**
 * Botão de ação canônico dos MFEs (primário, padrão, ghost e link inline).
 *
 * CSS: `styles/action-controls.css` (`.delpi-ui-action-btn*`).
 */
export function ActionButton({
  children,
  variant = "default",
  type = "button",
  disabled = false,
  onClick,
  className,
  "aria-label": ariaLabel,
}: ActionButtonProps) {
  const rootClass = [
    "delpi-ui-action-btn",
    variant !== "default" ? `delpi-ui-action-btn--${variant}` : null,
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
    >
      {children}
    </button>
  );
}
