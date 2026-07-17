import type { ButtonHTMLAttributes, ReactNode } from "react";

export type IconButtonTone = "default" | "danger";

export type IconButtonProps = {
  children: ReactNode;
  "aria-label": string;
  tone?: IconButtonTone;
  type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
};

/**
 * Botão só com ícone (remover item, fechar, etc.).
 *
 * CSS: `styles/action-controls.css` (`.delpi-ui-icon-btn*`).
 */
export function IconButton({
  children,
  "aria-label": ariaLabel,
  tone = "default",
  type = "button",
  disabled = false,
  onClick,
  className,
}: IconButtonProps) {
  const rootClass = [
    "delpi-ui-icon-btn",
    tone !== "default" ? `delpi-ui-icon-btn--${tone}` : null,
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
