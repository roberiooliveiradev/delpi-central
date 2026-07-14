import { DeckPropertySection } from "../deck/DeckPropertySection";
import { FormatRibbonTextBoxChrome } from "../formatRibbon/FormatRibbonTextBoxChrome";
import type { SelectionSectionLayout } from "./types";

/** Caixa de texto — preenchimento e contorno (heading/text). */
export function TextBoxSection({ layout }: { layout: SelectionSectionLayout }) {
  if (layout === "pane") {
    return (
      <DeckPropertySection title="Caixa" defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-text-box">
          <FormatRibbonTextBoxChrome bare />
        </div>
      </DeckPropertySection>
    );
  }
  return <FormatRibbonTextBoxChrome />;
}
