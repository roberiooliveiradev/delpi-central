import type { ReactNode } from "react";

export function DeckInspectorLayout({ children }: { children: ReactNode }) {
  return <div className="td-deck-inspector">{children}</div>;
}
