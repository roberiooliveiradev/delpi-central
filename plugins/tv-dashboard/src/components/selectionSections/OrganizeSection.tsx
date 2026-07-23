import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { FormatRibbonOrganizeGroup } from "../formatRibbon/FormatRibbonOrganizeGroup";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Organizar — camadas, alinhar, agrupar, girar (padrão Excel). */
export function OrganizeSection({
  layout,
}: {
  layout: SelectionSectionLayout;
  labels?: Labels;
}) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Organizar" hint={H.organize} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-organize">
          <FormatRibbonOrganizeGroup embed />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonOrganizeGroup />;
}

/**
 * @deprecated Conteúdo migrado para FormatRibbonOrganizeGroup.
 * Mantido como no-op para hosts que ainda resolvem `alignMulti`.
 */
export function AlignMultiSection(_props: { layout: SelectionSectionLayout }) {
  return null;
}
