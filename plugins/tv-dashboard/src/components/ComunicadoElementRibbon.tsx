import { resolveObjectRibbonTab } from "../utils/resolveObjectRibbonTab";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoShapeRibbon } from "./ComunicadoShapeRibbon";
import { ComunicadoTableDesignRibbon } from "./ComunicadoTableDesignRibbon";
import { SelectionSectionsHost } from "./selectionSections";

/**
 * Aba Elemento (top bar) — tipografia, chrome e organização conforme o tipo.
 * Com parte chart/tabela: host full (partFormat).
 */
export function ComunicadoElementRibbon() {
  const {
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
  } = useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
  });
  /* KPI/filtro parte → ShapeRibbon; chart/tabela → host partFormat. */
  if (
    isPartSelectionChrome(selectionChrome) &&
    selectionChrome.source !== "kpi" &&
    selectionChrome.source !== "input"
  ) {
    return (
      <DeckRibbonGroups className="td-deck-ribbon__groups--part">
        <SelectionSectionsHost layout="ribbon" full />
      </DeckRibbonGroups>
    );
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
