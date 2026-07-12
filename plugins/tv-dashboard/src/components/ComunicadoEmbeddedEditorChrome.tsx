import { useEffect, useState } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import {
  isSelectionPanelTab,
  normalizeSelectionRibbonTab,
} from "../utils/normalizeSelectionRibbonTab";

import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  DeckRibbonShell,
  isContextualDeckRibbonTab,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deck";

type Labels = Record<string, string>;

type EmbeddedTab = "insert" | "element" | "data" | "layers" | "view";

type Props = {
  labels?: Labels;
};

/** Chrome compacto do compositor embutido — mesmas faixas do deck. */
export function ComunicadoEmbeddedEditorChrome({ labels = {} }: Props) {
  const editor = useComunicadoEditor();
  const hasSelection = editor.selectedIds.length > 0;
  const tabs = resolveEmbeddedComunicadoRibbonTabs({ hasSelection });
  const [activeTab, setActiveTab] = useState<EmbeddedTab>("insert");

  useComunicadoRibbonTabSync((tab) => {
    const normalized = normalizeSelectionRibbonTab(tab);
    if (
      normalized === "insert" ||
      normalized === "element" ||
      normalized === "data" ||
      normalized === "layers" ||
      normalized === "view"
    ) {
      setActiveTab(normalized);
    }
  });

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab(hasSelection ? editor.selectionPanelTab : "insert");
    }
  }, [activeTab, tabs, hasSelection, editor.selectionPanelTab]);

  useEffect(() => {
    if (!hasSelection) return;
    if (isSelectionPanelTab(editor.selectionPanelTab)) {
      setActiveTab(editor.selectionPanelTab);
    }
  }, [editor.selectionPanelTab, hasSelection]);

  function selectTab(tab: EmbeddedTab) {
    setActiveTab(tab);
    if (isSelectionPanelTab(tab)) {
      editor.setSelectionPanelTab(tab);
      editor.setDataPanelOpen(tab === "data");
    }
  }

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
                icon={tab.icon}
                active={activeTab === tab.id}
                onSelect={() => selectTab(tab.id as EmbeddedTab)}
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
