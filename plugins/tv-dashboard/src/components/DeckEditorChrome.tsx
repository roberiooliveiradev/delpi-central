import { useEffect, useState, type ReactNode } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import {
  isSelectionPanelTab,
  normalizeSelectionRibbonTab,
} from "../utils/normalizeSelectionRibbonTab";
import { DECK_TAB_KEYTIPS } from "../utils/deckKeyTips";
import { useOptionalComunicadoEditor } from "./comunicadoEditorContext";
import { DeckKeyTip } from "./DeckKeyTip";

import type { BranchScope, NativeScreenCatalogItem, Playlist, Slide } from "../api/tvDashboardApi";
import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { DeckSettingsPanel } from "./DeckSettingsPanel";
import { SlideDeckRibbon } from "./SlideDeckRibbon";
import { ComunicadoLayersPanel } from "./deck/ComunicadoLayersPanel";
import { Modal } from "./ui/Modal";
import {
  ComunicadoSlideBackgroundRibbon,
  DeckHistoryTabActions,
  DeckRibbonShell,
  isContextualDeckRibbonTab,
  type DeckRibbonTabId,
  resolveDeckRibbonTabs,
} from "./deck";

import type { DeckHomePlaylistChromeProps } from "./deck";

type SlideDeckProps = {
  slides: Slide[];
  selectedSlide: Slide | null;
  onAdd: () => void;
  onSelect: (slideId: string) => void;
  onDuplicate: (slide: Slide) => void;
  onToggleActive: (slide: Slide) => void;
  onRemove: (slide: Slide) => void;
  onExportPng?: () => void;
  onExportPdf?: () => void;
  onExportPptx?: () => void;
  exportBusy?: boolean;
  playlistChrome?: DeckHomePlaylistChromeProps;
};

type Props = {
  playlist: Playlist;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  isCustomSlide: boolean;
  adminLabels?: Record<string, string>;
  slideTabExtra?: ReactNode;
  slideDeck: SlideDeckProps;
  onSavePlaylistSettings: (field: string, value: string | number | Record<string, unknown>) => void;
  onSaveSlide: (
    slide: Slide,
    payload: {
      title: string;
      durationSec: number;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string;
      transitionStyle?: string | null;
    },
  ) => void;
};

function isRibbonTab(
  tab: DeckRibbonTabId,
): tab is "home" | "insert" | "element" | "tableDesign" | "tableLayout" | "data" | "view" {
  return (
    tab === "home" ||
    tab === "insert" ||
    tab === "element" ||
    tab === "tableDesign" ||
    tab === "tableLayout" ||
    tab === "data" ||
    tab === "view"
  );
}

function isSettingsTab(tab: DeckRibbonTabId): tab is "slide" | "playlist" {
  return tab === "slide" || tab === "playlist";
}

function ribbonDensityFor(tab: DeckRibbonTabId): "band" | "fit" {
  return tab === "element" || tab === "tableDesign" || tab === "tableLayout" ? "fit" : "band";
}

/** Chrome do editor: abas estilo PowerPoint + ribbon contextual + painel de configuração. */
export function DeckEditorChrome({
  playlist,
  slide,
  catalog,
  branchScope,
  isCustomSlide,
  adminLabels = {},
  slideTabExtra,
  slideDeck,
  onSavePlaylistSettings,
  onSaveSlide,
}: Props) {
  const editor = useOptionalComunicadoEditor();
  const hasSelection = Boolean(editor && editor.selectedIds.length > 0);
  const isTableSelection = editor?.selected?.type === "table_view";
  const tabs = resolveDeckRibbonTabs(isCustomSlide, { hasSelection, isTableSelection });
  const [activeTab, setActiveTab] = useState<DeckRibbonTabId>("home");
  const [layersModalOpen, setLayersModalOpen] = useState(false);

  function openLayersModal() {
    setLayersModalOpen(true);
    editor?.setSelectionPanelTab("layers");
  }

  function closeLayersModal() {
    setLayersModalOpen(false);
    if (editor?.selectionPanelTab === "layers") {
      editor.setSelectionPanelTab("element");
      if (hasSelection) setActiveTab(isTableSelection ? "tableDesign" : "element");
    }
  }

  useComunicadoRibbonTabSync((tab) => {
    const normalized = normalizeSelectionRibbonTab(tab);
    if (normalized === "layers") {
      openLayersModal();
      return;
    }
    if (normalized === "insert" || normalized === "data" || normalized === "view") {
      setLayersModalOpen(false);
      setActiveTab(normalized);
      return;
    }
    if (normalized === "element") {
      setLayersModalOpen(false);
      setActiveTab(isTableSelection ? "tableDesign" : "element");
    }
  });

  useEffect(() => {
    if (activeTab === "layers") {
      setActiveTab(hasSelection ? (isTableSelection ? "tableDesign" : "element") : "home");
      return;
    }
    if (!tabs.some((tab) => tab.id === activeTab)) {
      if (!hasSelection) {
        setActiveTab("home");
        return;
      }
      if (isTableSelection) {
        setActiveTab("tableDesign");
        return;
      }
      setActiveTab(
        editor?.selectionPanelTab === "layers"
          ? "element"
          : (editor?.selectionPanelTab ?? "element"),
      );
    }
  }, [activeTab, tabs, hasSelection, isTableSelection, editor?.selectionPanelTab]);

  useEffect(() => {
    if (!hasSelection || !isCustomSlide) return;
    if (isTableSelection) {
      if (activeTab === "element") setActiveTab("tableDesign");
      return;
    }
    if (activeTab === "tableDesign" || activeTab === "tableLayout") {
      setActiveTab("element");
    }
  }, [isTableSelection, hasSelection, isCustomSlide, activeTab]);

  useEffect(() => {
    const panelTab = editor?.selectionPanelTab;
    if (!hasSelection || !isCustomSlide || !panelTab) return;
    if (panelTab === "layers") {
      setLayersModalOpen(true);
      return;
    }
    setLayersModalOpen(false);
    if (panelTab === "element") {
      setActiveTab(isTableSelection ? "tableDesign" : "element");
      return;
    }
    setActiveTab(panelTab);
  }, [editor?.selectionPanelTab, hasSelection, isCustomSlide, isTableSelection]);

  useEffect(() => {
    if (activeTab === "slide" && !slide) {
      setActiveTab("home");
    }
  }, [activeTab, slide]);

  function selectTab(tab: DeckRibbonTabId) {
    if (tab === "layers") {
      openLayersModal();
      return;
    }
    setLayersModalOpen(false);
    setActiveTab(tab);
    if (tab === "tableDesign" || tab === "tableLayout") {
      editor?.setSelectionPanelTab("element");
      editor?.setDataPanelOpen(false);
      return;
    }
    if (isSelectionPanelTab(tab)) {
      editor?.setSelectionPanelTab(tab);
      editor?.setDataPanelOpen(tab === "data");
    }
  }

  const showRibbon = isRibbonTab(activeTab);

  return (
    <section className="td-deck-chrome" aria-label="Editor da programação">
      <div className="td-deck-chrome__head">
        <div className="td-deck-chrome__tabs" role="tablist" aria-label="Faixas do editor">
          <DeckHistoryTabActions />
          {tabs.map((tab, index) => {
            const contextual = isContextualDeckRibbonTab(tab);
            const firstContextual =
              contextual && tabs.slice(0, index).every((prev) => !isContextualDeckRibbonTab(prev));
            const tabActive =
              activeTab === tab.id || (tab.id === "layers" && layersModalOpen);
            return (
              <DeckKeyTip key={tab.id} letter={DECK_TAB_KEYTIPS[tab.id]} scope="tabs" placement="bottom">
                <TabHintCell
                  label={tab.label}
                  hint={tab.hint}
                  icon={tab.icon}
                  active={tabActive}
                  disabled={tab.disabledWhenNoSlide ? !slide : false}
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
              </DeckKeyTip>
            );
          })}
        </div>
      </div>

      {showRibbon ? (
        <div className="td-deck-chrome__ribbon">
          <DeckRibbonShell density={ribbonDensityFor(activeTab)}>
            {activeTab === "home" ? <SlideDeckRibbon {...slideDeck} /> : null}
            {isCustomSlide &&
            (activeTab === "insert" ||
              activeTab === "element" ||
              activeTab === "tableDesign" ||
              activeTab === "tableLayout" ||
              activeTab === "data" ||
              activeTab === "view") ? (
              <ComunicadoRibbonContent activeTab={activeTab} labels={adminLabels} />
            ) : null}
          </DeckRibbonShell>
        </div>
      ) : null}

      {isSettingsTab(activeTab) ? (
        <div
          className={[
            "td-deck-chrome__panel",
            "td-deck-chrome__panel--compact",
            activeTab === "slide" && isCustomSlide ? "td-deck-chrome__panel--slide-unified" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          role="tabpanel"
        >
          {activeTab === "slide" && isCustomSlide ? (
            <>
              <DeckRibbonShell label="Fundo da tela" embedded density="fit">
                <ComunicadoSlideBackgroundRibbon labels={adminLabels} />
              </DeckRibbonShell>
              <div className="td-deck-chrome__slide-strip-sep" aria-hidden="true" />
            </>
          ) : null}
          <DeckSettingsPanel
            activeTab={activeTab}
            playlist={playlist}
            slide={slide}
            catalog={catalog}
            branchScope={branchScope}
            slideTabExtra={slideTabExtra}
            onSavePlaylistSettings={onSavePlaylistSettings}
            onSaveSlide={onSaveSlide}
          />
        </div>
      ) : null}

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
