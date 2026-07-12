import { useEffect, useState, type ReactNode } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import {
  isSelectionPanelTab,
  normalizeSelectionRibbonTab,
} from "../utils/normalizeSelectionRibbonTab";
import { useOptionalComunicadoEditor } from "./comunicadoEditorContext";

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
};

type Props = {
  playlist: Playlist;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  isCustomSlide: boolean;
  adminLabels?: Record<string, string>;
  slideTabExtra?: ReactNode;
  headerActions?: ReactNode;
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
): tab is "home" | "insert" | "element" | "data" | "view" {
  return (
    tab === "home" ||
    tab === "insert" ||
    tab === "element" ||
    tab === "data" ||
    tab === "view"
  );
}

function isSettingsTab(tab: DeckRibbonTabId): tab is "slide" | "playlist" {
  return tab === "slide" || tab === "playlist";
}

function ribbonDensityFor(tab: DeckRibbonTabId): "band" | "fit" {
  return tab === "element" || tab === "data" ? "fit" : "band";
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
  headerActions,
  slideDeck,
  onSavePlaylistSettings,
  onSaveSlide,
}: Props) {
  const editor = useOptionalComunicadoEditor();
  const hasSelection = Boolean(editor && editor.selectedIds.length > 0);
  const tabs = resolveDeckRibbonTabs(isCustomSlide, { hasSelection });
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
    if (activeTab === "layers") {
      setActiveTab(hasSelection ? "element" : "home");
      return;
    }
    if (!tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab(hasSelection ? (editor?.selectionPanelTab === "layers" ? "element" : (editor?.selectionPanelTab ?? "element")) : "home");
    }
  }, [activeTab, tabs, hasSelection, editor?.selectionPanelTab]);

  useEffect(() => {
    const panelTab = editor?.selectionPanelTab;
    if (!hasSelection || !isCustomSlide || !panelTab) return;
    if (panelTab === "layers") {
      setLayersModalOpen(true);
      return;
    }
    setLayersModalOpen(false);
    setActiveTab(panelTab);
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
              <TabHintCell
                key={tab.id}
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
            );
          })}
        </div>
        {headerActions}
      </div>

      {showRibbon ? (
        <div className="td-deck-chrome__ribbon">
          <DeckRibbonShell density={ribbonDensityFor(activeTab)}>
            {activeTab === "home" ? <SlideDeckRibbon {...slideDeck} /> : null}
            {isCustomSlide &&
            (activeTab === "insert" ||
              activeTab === "element" ||
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
