import type { ReactNode } from "react";

export type BackLinkProps = {
  children: ReactNode;
  onClick: () => void;
  className?: string;
  variant?: "default" | "prominent";
};

/**
 * Link de navegação «voltar» com seta, usado no topo das páginas.
 *
 * CSS: `styles/action-controls.css` (`.delpi-ui-back-link`).
 */
export function BackLink({
  children,
  onClick,
  className,
  variant = "default",
}: BackLinkProps) {
  const rootClass = [
    "delpi-ui-back-link",
    variant === "prominent" ? "delpi-ui-back-link--prominent" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button type="button" className={rootClass} onClick={onClick}>
      <span className="delpi-ui-back-link__arrow" aria-hidden={true}>
        ←
      </span>
      {children}
    </button>
  );
}
