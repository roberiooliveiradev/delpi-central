import { resolveObjectRibbonTab } from "../utils/resolveObjectRibbonTab";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoShapeRibbon } from "./ComunicadoShapeRibbon";
import { ComunicadoTableRibbon } from "./ComunicadoTableRibbon";

/**
 * Aba Elemento (top bar) — mesmos domínios do painel lateral Elemento:
 * tipografia, chrome visual, posição e organização conforme o tipo selecionado.
 */
export function ComunicadoElementRibbon() {
  const { selected, selectedChartPart, selectedKpiPart } = useComunicadoEditor();
  const kind = resolveObjectRibbonTab({
    selected,
    selectedChartPart,
    selectedKpiPart,
  });

  if (kind === "chart") return <ComunicadoChartRibbon />;
  if (kind === "table") return <ComunicadoTableRibbon />;
  return <ComunicadoShapeRibbon />;
}
