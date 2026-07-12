import { useEffect, useState, type ReactNode } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import { useOptionalComunicadoEditor } from "./comunicadoEditorContext";

import type { BranchScope, NativeScreenCatalogItem, Playlist, Slide } from "../api/tvDashboardApi";
import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { DeckSettingsPanel } from "./DeckSettingsPanel";
import { SlideDeckRibbon } from "./SlideDeckRibbon";
import {
  ComunicadoSlideBackgroundRibbon,
  DeckHistoryTabActions,
  DeckRibbonShell,
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
): tab is "home" | "insert" | "format" | "chart" | "shape" | "view" {
  return (
    tab === "home" ||
    tab === "insert" ||
    tab === "format" ||
    tab === "chart" ||
    tab === "shape" ||
    tab === "view"
  );
}

function isSettingsTab(tab: DeckRibbonTabId): tab is "slide" | "playlist" {
  return tab === "slide" || tab === "playlist";
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
  const chartSelected = editor?.selected?.type === "chart_view";
  const shapeSelected = editor?.selected?.type === "shape";
  const chartPartPrimitiveSelected = Boolean(
    chartSelected &&
      editor?.selectedChartPart &&
      ["marker", "series", "chartArea", "plotArea", "axis", "grid"].includes(
        editor.selectedChartPart.kind,
      ),
  );
  const tabs = resolveDeckRibbonTabs(isCustomSlide, {
    chartSelected,
    shapeSelected,
    chartPartPrimitiveSelected,
  });
  const [activeTab, setActiveTab] = useState<DeckRibbonTabId>("home");

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

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab(
        chartPartPrimitiveSelected
          ? "shape"
          : chartSelected
            ? "chart"
            : shapeSelected
              ? "shape"
              : "home",
      );
    }
  }, [activeTab, tabs, chartSelected, shapeSelected, chartPartPrimitiveSelected]);

  useEffect(() => {
    if (chartPartPrimitiveSelected && isCustomSlide) {
      setActiveTab("shape");
    } else if (chartSelected && isCustomSlide) {
      setActiveTab("chart");
    } else if (shapeSelected && isCustomSlide) {
      setActiveTab("shape");
    }
  }, [
    chartSelected,
    shapeSelected,
    chartPartPrimitiveSelected,
    isCustomSlide,
    editor?.selectedId,
    editor?.selectedChartPart,
  ]);

  useEffect(() => {
    if (activeTab === "slide" && !slide) {
      setActiveTab("home");
    }
  }, [activeTab, slide]);

  return (
    <section className="td-deck-chrome" aria-label="Editor da programação">
      <div className="td-deck-chrome__head">
        <div className="td-deck-chrome__tabs" role="tablist" aria-label="Faixas do editor">
          <DeckHistoryTabActions />
          {tabs.map((tab) => (
            <TabHintCell
              key={tab.id}
              label={tab.label}
              hint={tab.hint}
              active={activeTab === tab.id}
              disabled={tab.disabledWhenNoSlide ? !slide : false}
              onSelect={() => setActiveTab(tab.id)}
              cellClassName="td-deck-chrome__tab-cell"
              tabClassName="td-deck-chrome__tab"
              tabActiveClassName="td-deck-chrome__tab--active"
            />
          ))}
        </div>
        {headerActions}
      </div>

      {isRibbonTab(activeTab) ? (
        <div className="td-deck-chrome__ribbon">
          <DeckRibbonShell>
            {activeTab === "home" ? <SlideDeckRibbon {...slideDeck} /> : null}
            {isCustomSlide &&
            (activeTab === "insert" ||
              activeTab === "format" ||
              activeTab === "chart" ||
              activeTab === "shape" ||
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
              <DeckRibbonShell label="Fundo da tela" embedded>
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
    </section>
  );
}
