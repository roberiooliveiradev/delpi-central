import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  variant?: "default" | "side";
};

export function DeckInspectorLayout({ children, variant = "default" }: Props) {
  const className =
    variant === "side" ? "td-deck-inspector td-deck-inspector--side" : "td-deck-inspector";
  return <div className={className}>{children}</div>;
}
