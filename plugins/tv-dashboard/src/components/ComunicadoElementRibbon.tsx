import { resolveObjectRibbonTab } from "../utils/resolveObjectRibbonTab";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoPartFormatRibbon } from "./ComunicadoPartFormatRibbon";
import { ComunicadoShapeRibbon } from "./ComunicadoShapeRibbon";
import { ComunicadoTableDesignRibbon } from "./ComunicadoTableDesignRibbon";

/**
 * Aba Elemento (top bar) — tipografia, chrome e organização conforme o tipo.
 * Com parte selecionada: só chrome da parte (não misturar com layout global).
 */
export function ComunicadoElementRibbon() {
  const { selected, selectedChartPart, selectedKpiPart, selectedTablePart } =
    useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
  });
  /* KPI parte → ShapeRibbon (já tem Aparência); chart/tabela → PartFormatRibbon. */
  if (isPartSelectionChrome(selectionChrome) && selectionChrome.source !== "kpi") {
    return <ComunicadoPartFormatRibbon chrome={selectionChrome} />;
  }

  const kind = resolveObjectRibbonTab({
    selected,
    selectedChartPart,
    selectedKpiPart,
  });

  if (kind === "chart") return <ComunicadoChartRibbon />;
  if (kind === "table") return <ComunicadoTableDesignRibbon />;
  return <ComunicadoShapeRibbon />;
}
