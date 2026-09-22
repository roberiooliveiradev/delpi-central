import { useRibbonSectionPopoverSurface } from "@delpi/plugin-ui/index";
import { Palette } from "lucide-react";
import {
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  type ComunicadoBlock,
  type ComunicadoKpiOptions,
  type ComunicadoKpiViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS as H } from "../../content/helpTooltips";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTilePopover } from "../deck/DeckRibbonTilePopover";
import { KpiColorsStylesMenu } from "../KpiColorsStylesMenu";
import { KpiViewOptionsInspector } from "../KpiViewOptionsInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import type { SelectionSectionLayout } from "./types";

/**
 * Aparência / elementos do KPI.
 * Pane: inspetor completo. Ribbon: tile + popover (paridade com tableStyles / chartStyles).
 * O menu `KpiColorsStylesMenu` é chrome de painel — nunca embutir na band de 112px.
 */
export function KpiAppearanceSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "kpi_view") return null;

  const block = selected as ComunicadoKpiViewBlock;
  const options = mergeComunicadoKpiOptions({
    ...block.kpiOptions,
    ...partsToKpiOptions(block.kpiParts),
  });
  const persistOptions = (nextOptions: ComunicadoKpiOptions) => {
    updateSelected({
      kpiOptions: nextOptions,
      kpiParts: mergeKpiPartsWithOptions(block.kpiParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  if (layout === "pane") {
    return <KpiViewOptionsInspector pane />;
  }

  return (
    <DeckRibbonGroup groupId="kpi-appearance" label="Estilos" hint={H.ribbon.kpiAppearance}>
      <KpiAppearanceBandOrInline options={options} onApplyOptions={persistOptions} />
    </DeckRibbonGroup>
  );
}

function KpiAppearanceBandOrInline({
  options,
  onApplyOptions,
}: {
  options: ComunicadoKpiOptions;
  onApplyOptions: (next: ComunicadoKpiOptions) => void;
}) {
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const stylesMenu = (close?: () => void) => (
    <div className="td-chart-float__popover td-chart-float__popover--style">
      <KpiColorsStylesMenu
        options={options}
        onApplyOptions={(next) => {
          onApplyOptions(mergeComunicadoKpiOptions(next));
          close?.();
        }}
      />
    </div>
  );

  if (inSectionPopover) {
    return stylesMenu();
  }

  return (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTilePopover
        icon={Palette}
        label="Alterar estilos"
        hint={H.ribbon.kpiAppearance}
        panelLabel="Estilos de aparência do KPI"
        panelVariant="menu"
        panelClassName="td-chart-float__popover--style"
      >
        {(close) => stylesMenu(close)}
      </DeckRibbonTilePopover>
    </div>
  );
}
