import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { FormatRibbonTextBoxChrome } from "../formatRibbon/FormatRibbonTextBoxChrome";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Caixa de texto — preenchimento e contorno (heading/text). */
export function TextBoxSection({ layout }: { layout: SelectionSectionLayout }) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Caixa" hint={H.box} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-text-box">
          <FormatRibbonTextBoxChrome bare />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonTextBoxChrome />;
}
