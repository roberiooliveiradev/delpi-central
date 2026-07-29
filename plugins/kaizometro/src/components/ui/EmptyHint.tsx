import type { ReactNode } from "react";

type EmptyHintProps = {
  children: ReactNode;
  className?: string;
};

/** Texto auxiliar vazio / sem dados (BEM `kz-empty-hint`). */
export function EmptyHint({ children, className }: EmptyHintProps) {
  const rootClass = ["kz-empty-hint", className].filter(Boolean).join(" ");
  return <p className={rootClass}>{children}</p>;
}
