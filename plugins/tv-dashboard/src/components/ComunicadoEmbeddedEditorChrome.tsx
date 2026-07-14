import { useEffect, useState } from "react";
import { TabHintCell, TabPanelTransition } from "@delpi/plugin-ui/index";
import { isDataBoundEditorBlockType } from "@delpi/tv-dashboard-presentation";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import {
  isSelectionPanelTab,
  normalizeSelectionRibbonTab,
} from "../utils/normalizeSelectionRibbonTab";

import {
  ComunicadoRibbonContent,
  type ComunicadoRibbonContentTab,
} from "./ComunicadoRibbonContent";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  DeckRibbonShell,
  isContextualDeckRibbonTab,
  resolveEmbeddedComunicadoRibbonTabs,
  type DeckRibbonTabId,
} from "./deck";

type Labels = Record<string, string>;

type RibbonEmbeddedTab =
  | "insert"
  | "element"
  | "tableDesign"
  | "tableLayout"
  | "data"
  | "view"
  | "layers";

type Props = {
  labels?: Labels;
};

function ribbonDensityFor(tab: RibbonEmbeddedTab): "band" | "fit" {
  return tab === "element" || tab === "tableDesign" || tab === "tableLayout" ? "fit" : "band";
}

function hasRibbonBody(tab: RibbonEmbeddedTab): boolean {
  return tab !== "layers";
}

/** Chrome compacto do compositor embutido — mesmas faixas do deck. */
export function ComunicadoEmbeddedEditorChrome({ labels = {} }: Props) {
  const editor = useComunicadoEditor();
  const hasSelection = editor.selectedIds.length > 0;
  const isTableSelection = editor.selected?.type === "table_view";
  const hasDataBoundSelection = Boolean(
    editor.selected && isDataBoundEditorBlockType(editor.selected.type),
  );
  const showDataTab = editor.dataPanelOpen || hasDataBoundSelection;
  const tabs = resolveEmbeddedComunicadoRibbonTabs({
    hasSelection,
    isTableSelection,
    hasDataBoundSelection,
    showDataTab,
  });
  const [activeTab, setActiveTab] = useState<RibbonEmbeddedTab>("insert");

  useComunicadoRibbonTabSync((tab) => {
    const normalized = normalizeSelectionRibbonTab(tab);
    if (normalized === "layers") {
      editor.openLayersPanel();
      setActiveTab("layers");
      return;
    }
    if (normalized === "insert" || normalized === "data" || normalized === "view") {
      setActiveTab(normalized);
      return;
    }
    if (normalized === "tableDesign" || normalized === "tableLayout") {
      setActiveTab(normalized);
      return;
    }
    if (normalized === "element") {
      setActiveTab(isTableSelection ? "tableDesign" : "element");
    }
  });

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab(tabs.some((t) => t.id === "layers") ? "layers" : "insert");
    }
  }, [activeTab, tabs]);

  useEffect(() => {
    if (!hasSelection) return;
    if (isTableSelection && activeTab === "element") {
      setActiveTab("tableDesign");
      return;
    }
    if (!isTableSelection && (activeTab === "tableDesign" || activeTab === "tableLayout")) {
      setActiveTab("element");
    }
  }, [isTableSelection, hasSelection, activeTab]);

  useEffect(() => {
    if (editor.selectionPanelTab === "layers") {
      setActiveTab("layers");
      return;
    }
    if (editor.selectionPanelTab === "data") {
      setActiveTab("data");
      return;
    }
    if (
      editor.selectionPanelTab === "tableDesign" ||
      editor.selectionPanelTab === "tableLayout"
    ) {
      setActiveTab(editor.selectionPanelTab);
      return;
    }
    if (editor.selectionPanelTab === "element" && hasSelection) {
      setActiveTab(isTableSelection ? "tableDesign" : "element");
    }
  }, [editor.selectionPanelTab, hasSelection, isTableSelection]);

  function selectTab(tab: DeckRibbonTabId) {
    if (tab === "layers") {
      editor.openLayersPanel();
      setActiveTab("layers");
      return;
    }
    if (
      tab !== "insert" &&
      tab !== "element" &&
      tab !== "tableDesign" &&
      tab !== "tableLayout" &&
      tab !== "data" &&
      tab !== "view"
    ) {
      return;
    }
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
            const tabActive = activeTab === tab.id;
            return (
              <TabHintCell
                key={tab.id}
                label={tab.label}
                hint={tab.hint}
                icon={tab.icon}
                active={tabActive}
                onSelect={() => selectTab(tab.id)}
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

      {hasRibbonBody(activeTab) && activeTab !== "layers" ? (
        <div className="td-deck-chrome__ribbon">
          <TabPanelTransition tabKey={activeTab} className="td-deck-chrome__ribbon-panel">
            <DeckRibbonShell density={ribbonDensityFor(activeTab)}>
              <ComunicadoRibbonContent
                activeTab={activeTab as ComunicadoRibbonContentTab}
                labels={labels}
              />
            </DeckRibbonShell>
          </TabPanelTransition>
        </div>
      ) : null}
    </section>
  );
}
