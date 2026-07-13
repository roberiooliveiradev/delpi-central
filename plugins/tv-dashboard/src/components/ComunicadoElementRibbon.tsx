import { resolveObjectRibbonTab } from "../utils/resolveObjectRibbonTab";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoShapeRibbon } from "./ComunicadoShapeRibbon";
import { ComunicadoTableDesignRibbon } from "./ComunicadoTableDesignRibbon";

/**
 * Aba Elemento (top bar) — tipografia, chrome e organização conforme o tipo.
 * Tabela usa as abas Design/Layout no chrome; fallback aqui se Elemento abrir.
 */
export function ComunicadoElementRibbon() {
  const { selected, selectedChartPart, selectedKpiPart } = useComunicadoEditor();
  const kind = resolveObjectRibbonTab({
    selected,
    selectedChartPart,
    selectedKpiPart,
  });

  if (kind === "chart") return <ComunicadoChartRibbon />;
  if (kind === "table") return <ComunicadoTableDesignRibbon />;
  return <ComunicadoShapeRibbon />;
}
