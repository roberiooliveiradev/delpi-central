import { useState } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";

import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonShell, resolveEmbeddedComunicadoRibbonTabs } from "./deck";

type Labels = Record<string, string>;

type EmbeddedTab = "insert" | "format" | "chart" | "shape" | "view";

type Props = {
  labels?: Labels;
};

/** Chrome compacto do compositor embutido — mesmas faixas Inserir/Formatar/Gráfico/Forma do deck. */
export function ComunicadoEmbeddedEditorChrome({ labels = {} }: Props) {
  const { selected, selectedChartPart } = useComunicadoEditor();
  const chartSelected = selected?.type === "chart_view";
  const shapeSelected = selected?.type === "shape";
  const shapeChromeSelected =
    selected?.type === "kpi_view" || selected?.type === "table_view" || chartSelected;
  const chartPartPrimitiveSelected = Boolean(
    chartSelected &&
      selectedChartPart &&
      ["marker", "series", "chartArea", "plotArea", "axis", "grid"].includes(selectedChartPart.kind),
  );
  const tabs = resolveEmbeddedComunicadoRibbonTabs({
    chartSelected,
    shapeSelected,
    chartPartPrimitiveSelected,
    shapeChromeSelected,
  });
  const [activeTab, setActiveTab] = useState<EmbeddedTab>("insert");

  useComunicadoRibbonTabSync((tab) => {
    if (
      tab === "insert" ||
      tab === "format" ||
      tab === "chart" ||
      tab === "shape" ||
      tab === "view"
    ) {
      setActiveTab(tab);
    }
  });

  return (
    <section className="td-deck-chrome td-deck-chrome--embedded" aria-label="Editor do comunicado">
      <div className="td-deck-chrome__head">
        <div className="td-deck-chrome__tabs" role="tablist" aria-label="Faixas do editor">
          {tabs.map((tab) => (
            <TabHintCell
              key={tab.id}
              label={tab.label}
              hint={tab.hint}
              active={activeTab === tab.id}
              onSelect={() => setActiveTab(tab.id as EmbeddedTab)}
              cellClassName="td-deck-chrome__tab-cell"
              tabClassName="td-deck-chrome__tab"
              tabActiveClassName="td-deck-chrome__tab--active"
            />
          ))}
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
