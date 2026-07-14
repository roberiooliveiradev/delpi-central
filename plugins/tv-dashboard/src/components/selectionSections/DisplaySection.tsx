import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { FormatRibbonOrganizeDisplay } from "../formatRibbon/FormatRibbonOrganizeSection";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Exibição — opacidade e ajuste de mídia (após Caixa / chrome; antes de Posição). */
export function DisplaySection({ layout }: { layout: SelectionSectionLayout }) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Exibição" hint={H.display} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-display">
          <FormatRibbonOrganizeDisplay embed />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonOrganizeDisplay />;
}
