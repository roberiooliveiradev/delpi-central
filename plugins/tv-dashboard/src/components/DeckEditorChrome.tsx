import { useEffect, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { TabHintCell, TabPanelTransition } from "@delpi/plugin-ui/index";
import { isDataBoundEditorBlockType } from "@delpi/tv-dashboard-presentation";

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

function isRibbonContentTab(
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

/** Chrome do editor: abas + faixa contextual + painel de configuração. */
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
  const hasDataBoundSelection = Boolean(
    editor?.selected && isDataBoundEditorBlockType(editor.selected.type),
  );
  const showDataTab = Boolean(editor?.dataPanelOpen) || hasDataBoundSelection;
  const tabs = resolveDeckRibbonTabs(isCustomSlide, {
    hasSelection,
    isTableSelection,
    hasDataBoundSelection,
    showDataTab,
  });
  const [activeTab, setActiveTab] = useState<DeckRibbonTabId>("home");
  const [chromeCollapsed, setChromeCollapsed] = useState(() => readDeckChromeCollapsed());

  function setCollapsed(next: boolean) {
    setChromeCollapsed(next);
    writeDeckChromeCollapsed(next);
  }

  useComunicadoRibbonTabSync((tab) => {
    const normalized = normalizeSelectionRibbonTab(tab);
    if (normalized === "layers") {
      editor?.openLayersPanel();
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
    /* Aba sumiu (ex.: limpou seleção) → fallback. */
    if (!tabs.some((tab) => tab.id === activeTab)) {
      if (tabs.some((tab) => tab.id === "layers") && activeTab === "element") {
        setActiveTab("layers");
        return;
      }
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

  /** Sync bidirecional: painel lateral espelha na faixa (incluindo Elemento / Design·Layout). */
  useEffect(() => {
    const panelTab = editor?.selectionPanelTab;
    if (!isCustomSlide || !panelTab) return;
    if (panelTab === "layers") {
      setActiveTab("layers");
      return;
    }
    if (panelTab === "data") {
      setActiveTab("data");
      return;
    }
    if (panelTab === "tableDesign" || panelTab === "tableLayout") {
      setActiveTab(panelTab);
      return;
    }
    if (panelTab === "element" && hasSelection) {
      setActiveTab(isTableSelection ? "tableDesign" : "element");
    }
  }, [editor?.selectionPanelTab, hasSelection, isCustomSlide, isTableSelection]);

  useEffect(() => {
    if (activeTab === "slide" && !slide) {
      setActiveTab("home");
    }
  }, [activeTab, slide]);

  function selectTab(tab: DeckRibbonTabId) {
    if (tab === "layers") {
      editor?.openLayersPanel();
      setActiveTab("layers");
      return;
    }
    setActiveTab(tab);
    if (isSelectionPanelTab(tab)) {
      editor?.setSelectionPanelTab(tab);
      editor?.setDataPanelOpen(tab === "data");
    }
  }

  const showRibbon = isRibbonContentTab(activeTab) && !chromeCollapsed;
  const playlistChrome = slideDeck.playlistChrome;
  const activeTabMeta = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  return (
    <section
      className={[
        "td-deck-chrome",
        chromeCollapsed ? "td-deck-chrome--truncated" : "",
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
                const tabActive = activeTab === tab.id;
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
    </section>
  );
}
