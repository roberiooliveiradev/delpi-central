import {
  chartPartAllowsFrame,
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
 * Tamanho e posição — só geometria + rotação.
 * Opacidade / objectFit ficam em `AppearanceSection` (Exibição) ou Forma.
 */
export function DisplaySection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, selectedChartPart, selectedIds } = useComunicadoEditor();

  if (
    selected &&
    selectedIds.length <= 1 &&
    selected.type === "chart_view" &&
    selectedChartPart &&
    !chartPartAllowsFrame(selectedChartPart)
  ) {
    /* Sem geometria — Exibição cobre opacidade; não renderizar Posição vazia. */
    return null;
  }

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tamanho e posição" hint={SIZE_POSITION_HINT} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-display td-selection-section--pane-frame">
          <FormatRibbonFrameSection density="full" embed includeOpacity={false} />
        </div>
      </SelectionPaneSection>
    );
  }
  return <FormatRibbonFrameSection density="full" includeOpacity={false} />;
}
