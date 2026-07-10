import { useState } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";

import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { DeckRibbonShell, resolveEmbeddedComunicadoRibbonTabs } from "./deck";

type Labels = Record<string, string>;

type EmbeddedTab = "insert" | "format" | "view";

type Props = {
  labels?: Labels;
};

/** Chrome compacto do compositor embutido — mesmas faixas Inserir/Formatar do deck. */
export function ComunicadoEmbeddedEditorChrome({ labels = {} }: Props) {
  const tabs = resolveEmbeddedComunicadoRibbonTabs();
  const [activeTab, setActiveTab] = useState<EmbeddedTab>("insert");

  useComunicadoRibbonTabSync(setActiveTab);

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
