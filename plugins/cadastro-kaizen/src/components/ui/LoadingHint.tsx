import type { ReactNode } from "react";

type LoadingHintProps = {
  children?: ReactNode;
  className?: string;
};

/** Indicador textual de carregamento inline (mesmo visual de `EmptyHint`). */
export function LoadingHint({ children = "Carregando…", className }: LoadingHintProps) {
  const rootClass = ["kz-empty-hint", className].filter(Boolean).join(" ");
  return (
    <p className={rootClass} role="status" aria-live="polite">
      {children}
    </p>
  );
}
