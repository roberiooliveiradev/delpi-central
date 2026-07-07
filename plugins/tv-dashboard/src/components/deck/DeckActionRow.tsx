import type { ReactNode } from "react";

export function DeckActionRow({ children }: { children: ReactNode }) {
  return <div className="td-deck-actions-row">{children}</div>;
}
