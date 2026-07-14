import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { FormatRibbonTypographySections } from "../formatRibbon/FormatRibbonTypographySections";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Tipografia (Fonte / Efeitos / Parágrafo) — ribbon e painel.
 * Efeitos: popover ancorado na ribbon (como Preench.); painel embutido na sidebar.
 */
export function TypographySection({ layout }: { layout: SelectionSectionLayout }) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tipografia" hint={H.font} defaultOpen>
        <div className="td-selection-section td-selection-section--pane-typography">
          <FormatRibbonTypographySections embed />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonTypographySections />;
}
