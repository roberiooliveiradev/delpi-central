import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  label?: string;
  embedded?: boolean;
};

export function DeckRibbonShell({ children, label = "Controles de slide", embedded }: Props) {
  return (
    <div
      className={[
        "td-deck-ribbon",
        "td-deck-ribbon--compact",
        embedded ? "td-deck-ribbon--embedded" : null,
      ]
        .filter(Boolean)
        .join(" ")}
      role="toolbar"
      aria-label={label}
    >
      {children}
    </div>
  );
}
