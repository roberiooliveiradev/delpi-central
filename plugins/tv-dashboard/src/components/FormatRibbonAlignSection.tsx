import {
  AlignHorizontalJustifyCenter,
  AlignHorizontalJustifyEnd,
  AlignHorizontalJustifyStart,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  AlignVerticalJustifyStart,
  Group,
  Spline,
  Ungroup,
} from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { LayoutAlignCommand } from "../utils/comunicadoLayoutAlign";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

type Props = {
  canDistribute: boolean;
  canGroup: boolean;
  canUngroup: boolean;
  canConnect: boolean;
  alignSelected: (command: LayoutAlignCommand) => void;
  groupSelected: () => void;
  ungroupSelected: () => void;
  connectSelected: () => void;
};

/** Seção Alinhar / Dist. / Agrupar / Conectar do ribbon de formato (seleção múltipla). */
export function FormatRibbonAlignSection({
  canDistribute,
  canGroup,
  canUngroup,
  canConnect,
  alignSelected,
  groupSelected,
  ungroupSelected,
  connectSelected,
}: Props) {
  return (
    <DeckRibbonGroup label="Alinhar" hint={H.alignSelection}>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        {(
          [
            ["align-left", AlignHorizontalJustifyStart, "Esquerda", H.alignSelectionLeft],
            ["align-center-h", AlignHorizontalJustifyCenter, "Centro H", H.alignSelectionCenterH],
            ["align-right", AlignHorizontalJustifyEnd, "Direita", H.alignSelectionRight],
            ["align-top", AlignVerticalJustifyStart, "Topo", H.alignSelectionTop],
            ["align-center-v", AlignVerticalJustifyCenter, "Centro V", H.alignSelectionCenterV],
            ["align-bottom", AlignVerticalJustifyEnd, "Base", H.alignSelectionBottom],
          ] as const
        ).map(([command, Icon, label, hint]) => (
          <DeckRibbonTile
            key={command}
            icon={Icon}
            label={label}
            hint={hint}
            onClick={() => alignSelected(command as LayoutAlignCommand)}
          />
        ))}
        <DeckRibbonTile
          icon={AlignHorizontalJustifyCenter}
          label="Dist. H"
          hint={H.distributeH}
          disabled={!canDistribute}
          onClick={() => alignSelected("distribute-h")}
        />
        <DeckRibbonTile
          icon={AlignVerticalJustifyCenter}
          label="Dist. V"
          hint={H.distributeV}
          disabled={!canDistribute}
          onClick={() => alignSelected("distribute-v")}
        />
        <DeckRibbonTile
          icon={Group}
          label="Agrupar"
          hint={H.groupSelection}
          disabled={!canGroup}
          onClick={groupSelected}
        />
        <DeckRibbonTile
          icon={Ungroup}
          label="Desagrupar"
          hint={H.ungroupSelection}
          disabled={!canUngroup}
          onClick={ungroupSelected}
        />
        <DeckRibbonTile
          icon={Spline}
          label="Conectar"
          hint={H.connectSelection}
          disabled={!canConnect}
          onClick={connectSelected}
        />
      </div>
    </DeckRibbonGroup>
  );
}
