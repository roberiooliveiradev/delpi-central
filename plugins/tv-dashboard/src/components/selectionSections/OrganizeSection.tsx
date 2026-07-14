import { canConnectBlocks } from "@delpi/tv-dashboard-presentation";

import { selectedHasGroup } from "../../utils/comunicadoGrouping";
import { DeckPropertySection } from "../deck/DeckPropertySection";
import { FormatRibbonAlignSection } from "../FormatRibbonAlignSection";
import { FormatRibbonOrganizeSection } from "../formatRibbon/FormatRibbonOrganizeSection";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import type { SelectionSectionLayout } from "./types";

type Labels = Record<string, string>;

/** Organizar / opacidade — mesma seção na ribbon e no painel. */
export function OrganizeSection({
  layout,
  labels = {},
}: {
  layout: SelectionSectionLayout;
  labels?: Labels;
}) {
  if (layout === "pane") {
    return (
      <DeckPropertySection title="Organizar" defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-organize">
          <FormatRibbonOrganizeSection labels={labels} />
        </div>
      </DeckPropertySection>
    );
  }
  return <FormatRibbonOrganizeSection labels={labels} />;
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
      <DeckPropertySection title="Alinhar" defaultOpen>
        {body}
      </DeckPropertySection>
    );
  }
  return body;
}
