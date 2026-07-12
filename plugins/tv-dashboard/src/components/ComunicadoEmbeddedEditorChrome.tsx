import { useState } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";
import { isDataBoundEditorBlockType } from "@delpi/tv-dashboard-presentation";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";

import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  DeckRibbonShell,
  isContextualDeckRibbonTab,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deck";

type Labels = Record<string, string>;

type EmbeddedTab = "insert" | "format" | "chart" | "table" | "shape" | "data" | "view";

type Props = {
  labels?: Labels;
};

/** Chrome compacto do compositor embutido — mesmas faixas do deck. */
export function ComunicadoEmbeddedEditorChrome({ labels = {} }: Props) {
  const { selected, selectedChartPart } = useComunicadoEditor();
  const chartSelected = selected?.type === "chart_view";
  const tableSelected = selected?.type === "table_view";
  const shapeSelected = selected?.type === "shape";
  const dataSelected = Boolean(selected && isDataBoundEditorBlockType(selected.type));
  const shapeChromeSelected =
    selected?.type === "kpi_view" || tableSelected || chartSelected;
  const chartPartPrimitiveSelected = Boolean(
    chartSelected &&
      selectedChartPart &&
      ["marker", "series", "chartArea", "plotArea", "axis", "grid"].includes(selectedChartPart.kind),
  );
  const tabs = resolveEmbeddedComunicadoRibbonTabs({
    chartSelected,
    tableSelected,
    shapeSelected,
    dataSelected,
    chartPartPrimitiveSelected,
    shapeChromeSelected,
  });
  const [activeTab, setActiveTab] = useState<EmbeddedTab>("insert");

  useComunicadoRibbonTabSync((tab) => {
    if (
      tab === "insert" ||
      tab === "format" ||
      tab === "chart" ||
      tab === "table" ||
      tab === "shape" ||
      tab === "data" ||
      tab === "view"
    ) {
      setActiveTab(tab);
    }
  });

  return (
    <section className="td-deck-chrome td-deck-chrome--embedded" aria-label="Editor do comunicado">
      <div className="td-deck-chrome__head">
        <div className="td-deck-chrome__tabs" role="tablist" aria-label="Faixas do editor">
          {tabs.map((tab, index) => {
            const contextual = isContextualDeckRibbonTab(tab);
            const firstContextual =
              contextual && tabs.slice(0, index).every((prev) => !isContextualDeckRibbonTab(prev));
            return (
              <TabHintCell
                key={tab.id}
                label={tab.label}
                hint={tab.hint}
                active={activeTab === tab.id}
                onSelect={() => setActiveTab(tab.id as EmbeddedTab)}
                cellClassName={[
                  "td-deck-chrome__tab-cell",
                  contextual ? "td-deck-chrome__tab-cell--contextual" : "",
                  firstContextual ? "td-deck-chrome__tab-cell--contextual-start" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                tabClassName={[
                  "td-deck-chrome__tab",
                  contextual ? "td-deck-chrome__tab--contextual" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                tabActiveClassName={[
                  "td-deck-chrome__tab--active",
                  contextual ? "td-deck-chrome__tab--contextual-active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              />
            );
          })}
        </div>
      </div>
      <div className="td-deck-chrome__ribbon">
        <DeckRibbonShell embedded>
          <ComunicadoRibbonContent activeTab={activeTab} labels={labels} />
        </DeckRibbonShell>
      </div>
    </section>
  );
}
