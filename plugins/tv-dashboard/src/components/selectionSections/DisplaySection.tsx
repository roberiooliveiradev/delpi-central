import {
  chartPartAllowsFrame,
  resolveKpiShapeChromePartRef,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { FormatRibbonFrameSection } from "../formatRibbon/FormatRibbonFrameSection";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const SIZE_POSITION_HINT =
  H.sizePosition ??
  "Posição, tamanho e rotação em pixels de design da página.";

/**
 * Opacidade (e raio) vivem na seção Forma — aqui só geometria + rotação,
 * exceto mídia/tipos sem Forma (opacidade + objectFit).
 */
function shouldIncludeOpacityInDisplay(
  selected: ReturnType<typeof useComunicadoEditor>["selected"],
  selectedKpiPart: ReturnType<typeof useComunicadoEditor>["selectedKpiPart"],
): boolean {
  if (!selected) return false;
  if (selected.type === "shape") return false;
  if (selected.type === "text" || selected.type === "heading") return false;
  if (selected.type === "input") return false;
  if (selected.type === "chart_view") return false;
  if (selected.type === "table_view") return false;
  if (selected.type === "kpi_view") {
    return resolveKpiShapeChromePartRef(selectedKpiPart) == null;
  }
  return true;
}

/**
 * Tamanho e posição — X/Y, largura, altura e rotação.
 * Ribbon: tile + popover; painel: campos no accordion.
 */
export function DisplaySection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, selectedKpiPart, selectedChartPart, selectedIds } =
    useComunicadoEditor();
  const includeOpacity = shouldIncludeOpacityInDisplay(selected, selectedKpiPart);

  if (
    selected &&
    selectedIds.length <= 1 &&
    selected.type === "chart_view" &&
    selectedChartPart &&
    !chartPartAllowsFrame(selectedChartPart) &&
    !includeOpacity
  ) {
    return null;
  }

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tamanho e posição" hint={SIZE_POSITION_HINT} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-display">
          <FormatRibbonFrameSection density="full" embed includeOpacity={includeOpacity} />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonFrameSection density="full" includeOpacity={includeOpacity} />;
}
