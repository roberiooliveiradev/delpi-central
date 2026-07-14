import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { FormatRibbonElementActions } from "../formatRibbon/FormatRibbonOrganizeSection";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Ações — duplicar, remover (+ mídia: recorte/biblioteca/upload).
 * Ribbon e painel.
 */
export function ActionsSection({
  layout,
  labels = {},
}: {
  layout: SelectionSectionLayout;
  labels?: Record<string, string>;
}) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Ações" hint={H.actions ?? H.duplicateBlock} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-actions">
          <FormatRibbonElementActions labels={labels} embed />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonElementActions labels={labels} />;
}
