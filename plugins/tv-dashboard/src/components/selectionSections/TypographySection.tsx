import { FormatRibbonTypographySections } from "../formatRibbon/FormatRibbonTypographySections";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

/**
 * Tipografia (Fonte / Efeitos / Parágrafo) — mesma fonte na ribbon e no painel.
 */
export function TypographySection({ layout }: { layout: SelectionSectionLayout }) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tipografia" defaultOpen>
        <div className="td-selection-section td-selection-section--pane-typography">
          <FormatRibbonTypographySections embed />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonTypographySections />;
}
