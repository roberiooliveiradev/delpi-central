import { useEffect, useState, type ReactNode } from "react";
import { TabPanelTransition } from "@delpi/plugin-ui/index";
import { isDataBoundEditorBlockType } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import { clearLegacyDeckChromeCollapsed } from "../utils/deckChromeLayout";
import {
  isSelectionPanelTab,
  normalizeSelectionRibbonTab,
} from "../utils/normalizeSelectionRibbonTab";
import { DECK_TAB_KEYTIPS } from "../utils/deckKeyTips";
import { useOptionalComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import { DeckKeyTip } from "./DeckKeyTip";

import type { BranchScope, NativeScreenCatalogItem, Playlist, Slide } from "../api/tvDashboardApi";
import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { DeckSettingsPanel } from "./DeckSettingsPanel";
import { SlideCurrentRibbon } from "./SlideCurrentRibbon";
import {
  ComunicadoSlideBackgroundRibbon,
  DeckChromeTabsRow,
  DeckHistoryTabActions,
  DeckHomePlaylistChrome,
  DeckPlaylistIdentity,
  DeckRibbonShell,
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
  | "insert"
  | "element"
  | "tableDesign"
  | "tableLayout"
  | "data"
  | "view"
  | "slide"
  | "playlist" {
  return (
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

/** Preferência sem seleção / aba contextual sumiu: Inserir (custom) ou Programação. */
function resolveDefaultRibbonTab(
  tabs: { id: DeckRibbonTabId }[],
  isCustomSlide: boolean,
): DeckRibbonTabId {
  if (isCustomSlide && tabs.some((tab) => tab.id === "insert")) return "insert";
  if (tabs.some((tab) => tab.id === "playlist")) return "playlist";
  return tabs[0]?.id ?? "playlist";
}

/** Faixa contextual: altura estável (`band`) para não reflowar o palco ao selecionar. */
function ribbonDensityFor(_tab: DeckRibbonTabId): "band" | "fit" {
  return "band";
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
  const isCanvasTableSelection = editor?.selected?.type === "canvas_table";
  const tabs = resolveDeckRibbonTabs(isCustomSlide, {
    hasSelection,
    isTableSelection,
    hasDataBoundSelection,
    showDataTab,
  }).map((tab) =>
    tab.id === "element" && isCanvasTableSelection
      ? {
          ...tab,
          label: "Grade",
          hint:
            TV_DASHBOARD_HELP_TOOLTIPS.ribbonTabs.canvasTable ??
            "Ferramentas da Grade: estrutura, estilo e célula.",
        }
      : tab,
  );
  const [activeTab, setActiveTab] = useState<DeckRibbonTabId>(() =>
    isCustomSlide ? "insert" : "playlist",
  );

  useEffect(() => {
    clearLegacyDeckChromeCollapsed();
  }, []);

  useComunicadoRibbonTabSync((tab) => {
    const normalized = normalizeSelectionRibbonTab(tab);
    if (normalized === "layers") {
      editor?.openLayersPanel();
      /* Mantém a faixa atual (Inserir etc.) — Camadas não tem corpo de ribbon. */
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
    /* Aba sumiu (ex.: limpou seleção) → Inserir, não Camadas (sem corpo de ribbon). */
    if (!tabs.some((tab) => tab.id === activeTab) || activeTab === "layers") {
      setActiveTab(resolveDefaultRibbonTab(tabs, isCustomSlide));
    }
  }, [activeTab, tabs, isCustomSlide]);

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

  /** Sync bidirecional: painel lateral espelha na faixa (exceto Camadas). */
  useEffect(() => {
    const panelTab = editor?.selectionPanelTab;
    if (!isCustomSlide || !panelTab) return;
    if (panelTab === "layers") {
      /* Painel Camadas ≠ aba da top bar — não esconder o ribbon. */
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
      setActiveTab(resolveDefaultRibbonTab(tabs, isCustomSlide));
    }
  }, [activeTab, slide, tabs, isCustomSlide]);

  function selectTab(tab: DeckRibbonTabId) {
    if (tab === "layers") {
      editor?.openLayersPanel();
      /* Top bar permanece na aba com ribbon (Inserir por padrão). */
      if (!isRibbonContentTab(activeTab)) {
        setActiveTab(resolveDefaultRibbonTab(tabs, isCustomSlide));
      }
      return;
    }
    setActiveTab(tab);
    if (isSelectionPanelTab(tab)) {
      editor?.setSelectionPanelTab(tab);
      editor?.setDataPanelOpen(tab === "data");
    }
  }

  const showRibbon = isRibbonContentTab(activeTab);
  const playlistChrome = slideDeck.playlistChrome;

  return (
    <section
      className="td-deck-chrome"
      aria-label="Editor da programação"
      data-delpi-ui-density="compact"
    >
      <div className="td-deck-chrome__head">
        <DeckHistoryTabActions onBack={playlistChrome?.onBack} />
        <DeckChromeTabsRow
          tabs={tabs}
          activeTab={activeTab}
          onSelect={selectTab}
          isTabDisabled={(tab) => (tab.disabledWhenNoSlide ? !slide : false)}
          wrapTab={(tab, cell) => (
            <DeckKeyTip letter={DECK_TAB_KEYTIPS[tab.id]} scope="tabs" placement="bottom">
              {cell}
            </DeckKeyTip>
          )}
        />
        {playlistChrome ? (
          <div className="td-deck-chrome__head-trail">
            <DeckPlaylistIdentity
              playlistName={playlistChrome.playlistName}
              tvStatusLabel={playlistChrome.tvStatusLabel}
              tvStatusClass={playlistChrome.tvStatusClass}
            />
          </div>
        ) : null}
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
                <DeckRibbonGroups>
                  {activeTab === "playlist" && playlistChrome ? (
                    <DeckHomePlaylistChrome {...playlistChrome} />
                  ) : null}
                  {activeTab === "slide" ? (
                    <SlideCurrentRibbon
                      selectedSlide={slideDeck.selectedSlide}
                      onDuplicate={slideDeck.onDuplicate}
                      onToggleActive={slideDeck.onToggleActive}
                      onRemove={slideDeck.onRemove}
                      onExportPng={slideDeck.onExportPng}
                      onExportPdf={slideDeck.onExportPdf}
                      onExportPptx={slideDeck.onExportPptx}
                      exportBusy={slideDeck.exportBusy}
                    />
                  ) : null}
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
                </DeckRibbonGroups>
              ) : null}
            </DeckRibbonShell>
          </TabPanelTransition>
        </div>
      ) : null}
    </section>
  );
}
