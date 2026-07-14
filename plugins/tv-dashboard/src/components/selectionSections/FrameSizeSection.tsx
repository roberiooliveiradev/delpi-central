import { FormatRibbonFrameSection } from "../formatRibbon/FormatRibbonFrameSection";
import { DeckPropertySection } from "../deck/DeckPropertySection";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { SelectionSectionLayout } from "./types";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/**
 * Posição e tamanho — ribbon (compacto) e painel (accordion).
 * Fonte única: FormatRibbonFrameSection.
 */
export function FrameSizeSection({ layout }: { layout: SelectionSectionLayout }) {
  if (layout === "pane") {
    return (
      <DeckPropertySection title="Posição e tamanho" hint={E.position} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-frame">
          <FormatRibbonFrameSection density="full" />
        </div>
      </DeckPropertySection>
    );
  }
  return <FormatRibbonFrameSection density="compact" />;
}
