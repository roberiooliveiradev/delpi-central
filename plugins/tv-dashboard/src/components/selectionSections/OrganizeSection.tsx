import { canConnectBlocks } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { selectedHasGroup } from "../../utils/comunicadoGrouping";
import { FormatRibbonAlignSection } from "../FormatRibbonAlignSection";
import { FormatRibbonOrganizeLayers } from "../formatRibbon/FormatRibbonOrganizeSection";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Organizar — frente / fundo (camadas). */
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
          <FormatRibbonOrganizeLayers embed />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonOrganizeLayers />;
}

/** Multi-seleção: alinhamento/grupo. */
export function AlignMultiSection({ layout }: { layout: SelectionSectionLayout }) {
  const {
    blocks,
    selectedIds,
    alignSelected,
    groupSelected,
    ungroupSelected,
    connectSelected,
  } = useComunicadoEditor();

  const canDistribute = selectedIds.length >= 3;
  const canGroup = selectedIds.length >= 2;
  const canUngroup = selectedHasGroup(blocks, selectedIds);
  const canConnect = (() => {
    if (selectedIds.length !== 2) return false;
    const [idA, idB] = selectedIds;
    const a = blocks.find((block) => block.id === idA);
    const b = blocks.find((block) => block.id === idB);
    return Boolean(a && b && canConnectBlocks(a, b));
  })();

  const body = (
    <FormatRibbonAlignSection
      canDistribute={canDistribute}
      canGroup={canGroup}
      canUngroup={canUngroup}
      canConnect={canConnect}
      alignSelected={alignSelected}
      groupSelected={groupSelected}
      ungroupSelected={ungroupSelected}
      connectSelected={connectSelected}
    />
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Alinhar" hint={H.alignSelection} defaultOpen>
        {body}
      </SelectionPaneSection>
    );
  }
  return body;
}
