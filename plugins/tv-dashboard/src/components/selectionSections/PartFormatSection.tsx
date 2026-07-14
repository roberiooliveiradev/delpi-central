import type {
  ComunicadoChartViewBlock,
  ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../../utils/resolveSelectionChromeMode";
import { ChartRibbonShapeChrome } from "../formatRibbon/ChartRibbonShapeChrome";
import { TableRibbonShapeChrome } from "../formatRibbon/TableRibbonShapeChrome";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { PartSelectionNav } from "./PartSelectionNav";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

/**
 * Chrome da parte (gráfico/tabela) — nav + fill/outline da parte.
 * Tipografia/frame/organize vêm de outras seções do host.
 */
export function PartFormatSection({ layout }: { layout: SelectionSectionLayout }) {
  const {
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
    clearChartPartSelection,
    clearKpiPartSelection,
    clearTablePartSelection,
  } = useComunicadoEditor();

  const chromeMode = resolveSelectionChromeMode({
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
  });
  if (!isPartSelectionChrome(chromeMode)) return null;
  if (chromeMode.source === "kpi" || chromeMode.source === "input") return null;

  const onBack = () => {
    if (chromeMode.source === "chart") clearChartPartSelection();
    else if (chromeMode.source === "kpi") clearKpiPartSelection();
    else clearTablePartSelection();
  };

  const chromeBody = (
    <>
      {chromeMode.source === "chart" && selected?.type === "chart_view" ? (
        <ChartRibbonShapeChrome
          block={selected as ComunicadoChartViewBlock}
          embed={layout === "pane"}
        />
      ) : null}
      {chromeMode.source === "table" && selected?.type === "table_view" ? (
        <TableRibbonShapeChrome
          block={selected as ComunicadoTableViewBlock}
          embed={layout === "pane"}
        />
      ) : null}
    </>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection
        title={`Parte · ${chromeMode.partLabel}`}
        hint={`Controles desta parte do ${chromeMode.parentLabel.toLowerCase()}.`}
        defaultOpen
      >
        <PartSelectionNav chrome={chromeMode} onBack={onBack} />
        {/* Chromes já trazem tiles + sliders — não reenvolver em __tiles (vazava Raio/Opacidade). */}
        {chromeBody}
      </SelectionPaneSection>
    );
  }

  return (
    <>
      <PartSelectionNav chrome={chromeMode} onBack={onBack} />
      {chromeBody}
    </>
  );
}
