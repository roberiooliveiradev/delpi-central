import { DeckPropertySection } from "../deck/DeckPropertySection";
import { FormatRibbonTypographySections } from "../formatRibbon/FormatRibbonTypographySections";
import type { SelectionSectionLayout } from "./types";

/**
 * Tipografia (Fonte / Efeitos / Parágrafo) — mesma fonte na ribbon e no painel.
 */
export function TypographySection({ layout }: { layout: SelectionSectionLayout }) {
  const body = <FormatRibbonTypographySections />;
  if (layout === "pane") {
    return (
      <DeckPropertySection title="Tipografia" defaultOpen>
        <div className="td-selection-section td-selection-section--pane-typography">{body}</div>
      </DeckPropertySection>
    );
  }
  return body;
}
