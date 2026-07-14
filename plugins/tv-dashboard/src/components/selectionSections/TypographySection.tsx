import { FormatRibbonTypographySections } from "../formatRibbon/FormatRibbonTypographySections";
import type { SelectionSectionLayout } from "./types";

/**
 * Tipografia (Fonte / Efeitos / Parágrafo) — ribbon e painel.
 * No painel, cada grupo vira seção colapsável (via `embed` em FormatRibbonTypographySections).
 */
export function TypographySection({ layout }: { layout: SelectionSectionLayout }) {
  if (layout === "pane") {
    return (
      <div className="td-selection-section td-selection-section--pane-typography">
        <FormatRibbonTypographySections embed />
      </div>
    );
  }
  return <FormatRibbonTypographySections />;
}
