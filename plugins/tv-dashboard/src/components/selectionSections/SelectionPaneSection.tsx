import type { ReactNode } from "react";

import { DeckPropertySection } from "../deck/DeckPropertySection";

type Props = {
  title: string;
  hint?: string;
  defaultOpen?: boolean;
  children: ReactNode;
};

/**
 * Accordion do painel Elemento — sempre FormatPaneSection (colapsável).
 * Use em vez de DeckPropertySection sem `pane`.
 */
export function SelectionPaneSection({
  title,
  hint,
  defaultOpen = false,
  children,
}: Props) {
  return (
    <DeckPropertySection pane title={title} hint={hint} defaultOpen={defaultOpen}>
      {children}
    </DeckPropertySection>
  );
}
