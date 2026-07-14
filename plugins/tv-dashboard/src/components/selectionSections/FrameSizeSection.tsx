import { FormatRibbonFrameSection } from "../formatRibbon/FormatRibbonFrameSection";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/**
 * Posição e tamanho — ribbon (compacto) e painel (accordion colapsável).
 */
export function FrameSizeSection({ layout }: { layout: SelectionSectionLayout }) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Posição e tamanho" hint={E.position} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-frame">
          <FormatRibbonFrameSection density="compact" embed />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonFrameSection density="compact" />;
}
