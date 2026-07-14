import { useEffect, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { TabHintCell, TabPanelTransition } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import {
  readDeckChromeCollapsed,
  writeDeckChromeCollapsed,
} from "../utils/deckChromeLayout";
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
  DeckPlaylistIdentity,
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
): tab is
  | "home"
  | "insert"
  | "element"
  | "tableDesign"
  | "tableLayout"
  | "data"
  | "view"
  | "slide"
  | "playlist" {
  return (
    tab === "home" ||
    tab === "insert" ||
    tab === "element" ||
    tab === "tableDesign" ||
    tab === "tableLayout" ||
    tab === "data" ||
    tab === "view" ||
    tab === "slide" ||
    tab === "playlist"
  );
}

function ribbonDensityFor(tab: DeckRibbonTabId): "band" | "fit" {
  return tab === "element" ||
    tab === "tableDesign" ||
    tab === "tableLayout" ||
    tab === "slide" ||
    tab === "playlist"
    ? "fit"
    : "band";
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
  const [chromeCollapsed, setChromeCollapsed] = useState(() => readDeckChromeCollapsed());

  function setCollapsed(next: boolean) {
    setChromeCollapsed(next);
    writeDeckChromeCollapsed(next);
  }

  function openLayersModal() {
    setLayersModalOpen(true);
    editor?.setSelectionPanelTab("layers");
  }

  function closeLayersModal() {
    setLayersModalOpen(false);
    if (editor?.selectionPanelTab === "layers") {
      editor.setSelectionPanelTab("element");
      setActiveTab("home");
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
      setActiveTab("home");
      return;
    }
    /* Aba contextual sumiu (ex.: limpou seleção) → Página Inicial. */
    if (!tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab("home");
    }
  }, [activeTab, tabs]);

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

  /**
   * Painel lateral: só Camadas/Dados empurram a faixa.
   * «element» não força a ribbon — senão Gerenciar/F5 e «Página Inicial»
   * com seleção saltariam de volta para Elemento.
   * Troca para Elemento: clique na aba ou requestRibbonTab (seleção no palco).
   */
  useEffect(() => {
    const panelTab = editor?.selectionPanelTab;
    if (!hasSelection || !isCustomSlide || !panelTab) return;
    if (panelTab === "layers") {
      setLayersModalOpen(true);
      return;
    }
    setLayersModalOpen(false);
    if (panelTab === "data") {
      setActiveTab("data");
    }
  }, [editor?.selectionPanelTab, hasSelection, isCustomSlide]);

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

  const showRibbon = isRibbonTab(activeTab) && !chromeCollapsed;
  const playlistChrome = slideDeck.playlistChrome;
  const activeTabMeta = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  return (
    <section
      className={[
        "td-deck-chrome",
        chromeCollapsed ? "td-deck-chrome--collapsed" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Editor da programação"
    >
      {chromeCollapsed ? (
        <div className="td-deck-chrome__collapsed-rail">
          <button
            type="button"
            className="td-deck-chrome__reopen"
            onClick={() => setCollapsed(false)}
            aria-label="Expandir barra superior"
            title="Expandir faixa e ribbon"
          >
            <ChevronDown size={16} aria-hidden="true" />
          </button>
          <span className="td-deck-chrome__collapsed-label">
            {activeTabMeta?.label ?? "Editor"}
          </span>
          {playlistChrome ? (
            <DeckPlaylistIdentity
              playlistName={playlistChrome.playlistName}
              tvStatusLabel={playlistChrome.tvStatusLabel}
              tvStatusClass={playlistChrome.tvStatusClass}
            />
          ) : null}
        </div>
      ) : (
        <>
          <div className="td-deck-chrome__head">
            <div className="td-deck-chrome__tabs" role="tablist" aria-label="Faixas do editor">
              <DeckHistoryTabActions />
              {tabs.map((tab, index) => {
                const contextual = isContextualDeckRibbonTab(tab);
                const firstContextual =
                  contextual &&
                  tabs.slice(0, index).every((prev) => !isContextualDeckRibbonTab(prev));
                const tabActive =
                  activeTab === tab.id || (tab.id === "layers" && layersModalOpen);
                return (
                  <DeckKeyTip
                    key={tab.id}
                    letter={DECK_TAB_KEYTIPS[tab.id]}
                    scope="tabs"
                    placement="bottom"
                  >
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
            <div className="td-deck-chrome__head-trail">
              {playlistChrome ? (
                <DeckPlaylistIdentity
                  playlistName={playlistChrome.playlistName}
                  tvStatusLabel={playlistChrome.tvStatusLabel}
                  tvStatusClass={playlistChrome.tvStatusClass}
                />
              ) : null}
              <button
                type="button"
                className="td-deck-chrome__collapse"
                onClick={() => setCollapsed(true)}
                aria-label="Recolher barra superior"
                title="Recolher faixa e ribbon"
              >
                <ChevronUp size={16} aria-hidden="true" />
              </button>
            </div>
          </div>

          {showRibbon ? (
            <div className="td-deck-chrome__ribbon">
              <TabPanelTransition tabKey={activeTab} className="td-deck-chrome__ribbon-panel">
                <DeckRibbonShell
                  density={ribbonDensityFor(activeTab)}
                  label={
                    activeTab === "playlist"
                      ? "Programação"
                      : activeTab === "slide"
                        ? "Tela"
                        : "Controles de slide"
                  }
                >
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
                  {activeTab === "slide" || activeTab === "playlist" ? (
                    <div className="td-deck-ribbon__groups">
                      {activeTab === "slide" && isCustomSlide ? (
                        <ComunicadoSlideBackgroundRibbon labels={adminLabels} />
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
                </DeckRibbonShell>
              </TabPanelTransition>
            </div>
          ) : null}
        </>
      )}

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
