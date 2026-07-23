import {
  AlignHorizontalJustifyCenter,
  AlignHorizontalJustifyEnd,
  AlignHorizontalJustifyStart,
  AlignHorizontalSpaceAround,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  AlignVerticalJustifyStart,
  BringToFront,
  FlipHorizontal2,
  FlipVertical2,
  Grid3x3,
  Group,
  Magnet,
  MousePointer2,
  RotateCcw,
  RotateCw,
  SendToBack,
  Spline,
  Ungroup,
} from "lucide-react";
import { canConnectBlocks } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { selectedHasGroup } from "../../utils/comunicadoGrouping";
import type { LayoutAlignCommand } from "../../utils/comunicadoLayoutAlign";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonMenuTile, type DeckRibbonMenuItem } from "../deck/DeckRibbonMenuTile";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { useComunicadoEditor } from "../comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const C = TV_DASHBOARD_HELP_TOOLTIPS.contextMenu;
const V = TV_DASHBOARD_HELP_TOOLTIPS.view;

type Props = {
  /** Painel: omite caption do ribbon (accordion já titulou). */
  embed?: boolean;
};

/**
 * Grupo Organizar estilo Excel — uma linha:
 * Avançar▼ | Recuar▼ | Alinhar▼ | Agrupar▼ | Girar▼ | Painel
 */
export function FormatRibbonOrganizeGroup({ embed = false }: Props) {
  const {
    selected,
    selectedIds,
    blocks,
    bringForward,
    bringToFront,
    sendBackward,
    sendToBack,
    openLayersPanel,
    alignSelected,
    groupSelected,
    ungroupSelected,
    regroupSelected,
    lastUngroupedIds,
    connectSelected,
    rotateSelected,
    flipSelectedHorizontal,
    flipSelectedVertical,
    focusFrameRotationField,
    snapToGrid,
    setSnapToGrid,
    snapToObjects,
    setSnapToObjects,
    showStageGrid,
    setShowStageGrid,
  } = useComunicadoEditor();

  if (!selected) return null;

  const canDistribute = selectedIds.length >= 3;
  const canAlignSelection = selectedIds.length >= 2;
  const canGroup = selectedIds.length >= 2;
  const canUngroup = selectedHasGroup(blocks, selectedIds);
  const blockIdSet = new Set(blocks.map((block) => block.id));
  const canRegroup = lastUngroupedIds.filter((id) => blockIdSet.has(id)).length >= 2;
  const canConnect = (() => {
    if (selectedIds.length !== 2) return false;
    const [idA, idB] = selectedIds;
    const a = blocks.find((block) => block.id === idA);
    const b = blocks.find((block) => block.id === idB);
    return Boolean(a && b && canConnectBlocks(a, b));
  })();

  const alignItem = (
    id: LayoutAlignCommand,
    label: string,
    icon: DeckRibbonMenuItem["icon"],
    disabled: boolean,
    hint?: string,
    dividerBefore?: boolean,
  ): DeckRibbonMenuItem => ({
    id,
    label,
    icon,
    disabled,
    hint,
    dividerBefore,
    onSelect: () => alignSelected(id),
  });

  const forwardItems: DeckRibbonMenuItem[] = [
    {
      id: "bring-forward",
      label: C.bringForward,
      icon: BringToFront,
      onSelect: bringForward,
    },
    {
      id: "bring-to-front",
      label: C.bringToFront,
      icon: BringToFront,
      onSelect: bringToFront,
    },
  ];

  const backwardItems: DeckRibbonMenuItem[] = [
    {
      id: "send-backward",
      label: C.sendBackward,
      icon: SendToBack,
      onSelect: sendBackward,
    },
    {
      id: "send-to-back",
      label: C.sendToBack,
      icon: SendToBack,
      onSelect: sendToBack,
    },
  ];

  const alignItems: DeckRibbonMenuItem[] = [
    alignItem("align-left", "Alinhar à esquerda", AlignHorizontalJustifyStart, !canAlignSelection, H.alignSelectionLeft),
    alignItem("align-center-h", "Centralizar", AlignHorizontalJustifyCenter, !canAlignSelection, H.alignSelectionCenterH),
    alignItem("align-right", "Alinhar à direita", AlignHorizontalJustifyEnd, !canAlignSelection, H.alignSelectionRight),
    alignItem("align-top", "Alinhar parte superior", AlignVerticalJustifyStart, !canAlignSelection, H.alignSelectionTop, true),
    alignItem("align-center-v", "Alinhar ao meio", AlignVerticalJustifyCenter, !canAlignSelection, H.alignSelectionCenterV),
    alignItem("align-bottom", "Alinhar parte inferior", AlignVerticalJustifyEnd, !canAlignSelection, H.alignSelectionBottom),
    alignItem("distribute-h", "Distribuir na horizontal", AlignHorizontalJustifyCenter, !canDistribute, H.distributeH, true),
    alignItem("distribute-v", "Distribuir na vertical", AlignVerticalJustifyCenter, !canDistribute, H.distributeV),
    alignItem("align-slide-left", "Alinhar à esquerda do slide", AlignHorizontalJustifyStart, false, H.alignSlideLeft, true),
    alignItem("align-slide-center-h", "Centralizar no slide (H)", AlignHorizontalJustifyCenter, false, H.alignSlideCenterH),
    alignItem("align-slide-right", "Alinhar à direita do slide", AlignHorizontalJustifyEnd, false, H.alignSlideRight),
    alignItem("align-slide-top", "Alinhar ao topo do slide", AlignVerticalJustifyStart, false, H.alignSlideTop),
    alignItem("align-slide-center-v", "Centralizar no slide (V)", AlignVerticalJustifyCenter, false, H.alignSlideCenterV),
    alignItem("align-slide-bottom", "Alinhar à base do slide", AlignVerticalJustifyEnd, false, H.alignSlideBottom),
    {
      id: "snap-grid",
      label: "Ajustar à grade",
      icon: Magnet,
      dividerBefore: true,
      hint: V.snapToGrid,
      onSelect: () => setSnapToGrid(!snapToGrid),
    },
    {
      id: "snap-objects",
      label: "Ajustar a objetos",
      icon: AlignHorizontalSpaceAround,
      hint: V.snapToObjects,
      onSelect: () => setSnapToObjects(!snapToObjects),
    },
    {
      id: "show-grid",
      label: "Exibir linhas de grade",
      icon: Grid3x3,
      hint: V.grid,
      onSelect: () => setShowStageGrid(!showStageGrid),
    },
  ];

  const groupItems: DeckRibbonMenuItem[] = [
    {
      id: "group",
      label: "Agrupar",
      icon: Group,
      disabled: !canGroup,
      hint: H.groupSelection,
      onSelect: groupSelected,
    },
    {
      id: "regroup",
      label: "Reagrupar",
      icon: Group,
      disabled: !canRegroup,
      hint: H.regroupSelection,
      onSelect: regroupSelected,
    },
    {
      id: "ungroup",
      label: "Desagrupar",
      icon: Ungroup,
      disabled: !canUngroup,
      hint: H.ungroupSelection,
      onSelect: ungroupSelected,
    },
    {
      id: "connect",
      label: "Conectar",
      icon: Spline,
      disabled: !canConnect,
      hint: H.connectSelection,
      dividerBefore: true,
      onSelect: connectSelected,
    },
  ];

  const rotateItems: DeckRibbonMenuItem[] = [
    {
      id: "rotate-90-cw",
      label: "Girar 90° para a direita",
      icon: RotateCw,
      onSelect: () => rotateSelected(90),
    },
    {
      id: "rotate-90-ccw",
      label: "Girar 90° para a esquerda",
      icon: RotateCcw,
      onSelect: () => rotateSelected(-90),
    },
    {
      id: "flip-v",
      label: "Inverter verticalmente",
      icon: FlipVertical2,
      dividerBefore: true,
      onSelect: flipSelectedVertical,
    },
    {
      id: "flip-h",
      label: "Inverter horizontalmente",
      icon: FlipHorizontal2,
      onSelect: flipSelectedHorizontal,
    },
    {
      id: "more-rotation",
      label: "Mais opções de rotação…",
      icon: RotateCw,
      dividerBefore: true,
      hint: H.moreRotationOptions,
      onSelect: focusFrameRotationField,
    },
  ];

  return (
    <DeckRibbonGroup
      groupId="organize"
      label="Organizar"
      hint={H.organize}
      captionPlacement={embed ? "none" : "below"}
    >
      <div className="td-deck-ribbon__organize-grid">
        <DeckRibbonMenuTile
          icon={BringToFront}
          label="Avançar"
          hint={C.bringForward}
          onPrimaryClick={bringForward}
          items={forwardItems}
          menuAriaLabel="Avançar"
        />
        <DeckRibbonMenuTile
          icon={SendToBack}
          label="Recuar"
          hint={C.sendBackward}
          onPrimaryClick={sendBackward}
          items={backwardItems}
          menuAriaLabel="Recuar"
        />
        <DeckRibbonMenuTile
          icon={AlignHorizontalJustifyStart}
          label="Alinhar"
          hint={H.alignSelection}
          items={alignItems}
          menuAriaLabel="Alinhar"
        />
        <DeckRibbonMenuTile
          icon={Group}
          label="Agrupar"
          hint={H.groupSelection}
          onPrimaryClick={canGroup ? groupSelected : undefined}
          items={groupItems}
          menuAriaLabel="Agrupar"
        />
        <DeckRibbonMenuTile
          icon={RotateCw}
          label="Girar"
          hint={H.rotateMenu}
          onPrimaryClick={() => rotateSelected(90)}
          items={rotateItems}
          menuAriaLabel="Girar"
        />
        <DeckRibbonTile
          icon={MousePointer2}
          label="Painel"
          hint={H.selectionPane}
          onClick={() => openLayersPanel()}
        />
      </div>
    </DeckRibbonGroup>
  );
}

/** @deprecated Preferir FormatRibbonOrganizeGroup — mantido para imports legados. */
export function FormatRibbonOrganizeLayers({ embed = false }: Props) {
  return <FormatRibbonOrganizeGroup embed={embed} />;
}
