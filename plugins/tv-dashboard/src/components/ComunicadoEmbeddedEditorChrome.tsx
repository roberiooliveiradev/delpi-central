import { useEffect, useState } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import {
  isSelectionPanelTab,
  normalizeSelectionRibbonTab,
} from "../utils/normalizeSelectionRibbonTab";

import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoLayersPanel } from "./deck/ComunicadoLayersPanel";
import { Modal } from "./ui/Modal";
import {
  DeckRibbonShell,
  isContextualDeckRibbonTab,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deck";

type Labels = Record<string, string>;

type EmbeddedTab = "insert" | "element" | "data" | "layers" | "view";
type RibbonEmbeddedTab = "insert" | "element" | "data" | "view";

type Props = {
  labels?: Labels;
};

function ribbonDensityFor(tab: RibbonEmbeddedTab): "band" | "fit" {
  return tab === "element" ? "fit" : "band";
}

/** Chrome compacto do compositor embutido — mesmas faixas do deck. */
export function ComunicadoEmbeddedEditorChrome({ labels = {} }: Props) {
  const editor = useComunicadoEditor();
  const hasSelection = editor.selectedIds.length > 0;
  const tabs = resolveEmbeddedComunicadoRibbonTabs({ hasSelection });
  const [activeTab, setActiveTab] = useState<RibbonEmbeddedTab>("insert");
  const [layersModalOpen, setLayersModalOpen] = useState(false);

  function openLayersModal() {
    setLayersModalOpen(true);
    editor.setSelectionPanelTab("layers");
  }

  function closeLayersModal() {
    setLayersModalOpen(false);
    if (editor.selectionPanelTab === "layers") {
      editor.setSelectionPanelTab("element");
      if (hasSelection) setActiveTab("element");
    }
  }

  useComunicadoRibbonTabSync((tab) => {
    const normalized = normalizeSelectionRibbonTab(tab);
    if (normalized === "layers") {
      openLayersModal();
      return;
    }
    if (
      normalized === "insert" ||
      normalized === "element" ||
      normalized === "data" ||
      normalized === "view"
    ) {
      setLayersModalOpen(false);
      setActiveTab(normalized);
    }
  });

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeTab || (tab.id === "layers" && layersModalOpen))) {
      setActiveTab(hasSelection ? "element" : "insert");
    }
  }, [activeTab, tabs, hasSelection, layersModalOpen]);

  useEffect(() => {
    if (!hasSelection) return;
    if (editor.selectionPanelTab === "layers") {
      setLayersModalOpen(true);
      return;
    }
    if (isSelectionPanelTab(editor.selectionPanelTab)) {
      setLayersModalOpen(false);
      setActiveTab(editor.selectionPanelTab);
    }
  }, [editor.selectionPanelTab, hasSelection]);

  function selectTab(tab: EmbeddedTab) {
    if (tab === "layers") {
      openLayersModal();
      return;
    }
    setLayersModalOpen(false);
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
            const tabActive =
              activeTab === tab.id || (tab.id === "layers" && layersModalOpen);
            return (
              <TabHintCell
                key={tab.id}
                label={tab.label}
                hint={tab.hint}
                icon={tab.icon}
                active={tabActive}
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
        <DeckRibbonShell embedded density={ribbonDensityFor(activeTab)}>
          <ComunicadoRibbonContent activeTab={activeTab} labels={labels} />
        </DeckRibbonShell>
      </div>

      <Modal
        open={layersModalOpen}
        title="Camadas"
        onClose={closeLayersModal}
        className="td-modal--wide td-modal--layers"
      >
        <ComunicadoLayersPanel layout="pane" pane />
      </Modal>
    </section>
  );
}
