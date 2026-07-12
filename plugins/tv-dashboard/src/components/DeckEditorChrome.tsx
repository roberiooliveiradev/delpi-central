import { useEffect, useState, type ReactNode } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import { useComunicadoRibbonTabSync } from "../hooks/useComunicadoRibbonTabSync";
import { resolveSelectedTextFormatTarget } from "../utils/selectedTextFormatTarget";
import { useOptionalComunicadoEditor } from "./comunicadoEditorContext";

import type { BranchScope, NativeScreenCatalogItem, Playlist, Slide } from "../api/tvDashboardApi";
import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { DeckSettingsPanel } from "./DeckSettingsPanel";
import { SlideDeckRibbon } from "./SlideDeckRibbon";
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
): tab is "home" | "insert" | "format" | "chart" | "table" | "shape" | "data" | "view" {
  return (
    tab === "home" ||
    tab === "insert" ||
    tab === "format" ||
    tab === "chart" ||
    tab === "table" ||
    tab === "shape" ||
    tab === "data" ||
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
  const tableSelected = editor?.selected?.type === "table_view";
  const shapeSelected = editor?.selected?.type === "shape";
  const dataSelected = Boolean(
    editor?.selected &&
      (editor.selected.type === "chart_view" ||
        editor.selected.type === "table_view" ||
        editor.selected.type === "kpi_view" ||
        editor.selected.type === "data_source" ||
        editor.selected.type.startsWith("data_")),
  );
  const shapeChromeSelected =
    editor?.selected?.type === "kpi_view" ||
    tableSelected ||
    chartSelected;
  const chartPartPrimitiveSelected = Boolean(
    chartSelected &&
      editor?.selectedChartPart &&
      ["marker", "series", "chartArea", "plotArea", "axis", "grid"].includes(
        editor.selectedChartPart.kind,
      ),
  );
  const textFormatTarget = resolveSelectedTextFormatTarget({
    selected: editor?.selected ?? null,
    selectedKpiPart: editor?.selectedKpiPart,
    selectedChartPart: editor?.selectedChartPart,
  });
  // Eixo permanece primitivo de Forma; tipografia de título/legenda/KPI abre Formatar.
  const textPartFormatSelected =
    textFormatTarget?.mode === "part" && editor?.selectedChartPart?.kind !== "axis";
  /** Duplo clique em forma: manter Formatar (tipografia) em vez de forçar aba Forma. */
  const shapeTextEditing =
    Boolean(editor?.editingTextId) &&
    editor?.selected?.type === "shape" &&
    editor.editingTextId === editor.selected.id;
  const tabs = resolveDeckRibbonTabs(isCustomSlide, {
    chartSelected,
    tableSelected,
    shapeSelected,
    dataSelected,
    chartPartPrimitiveSelected,
    shapeChromeSelected,
  });
  const [activeTab, setActiveTab] = useState<DeckRibbonTabId>("home");

  useComunicadoRibbonTabSync((tab) => {
    if (
      tab === "insert" ||
      tab === "format" ||
      tab === "chart" ||
      tab === "table" ||
      tab === "shape" ||
      tab === "data" ||
      tab === "view"
    ) {
      setActiveTab(tab);
    }
  });

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab(
        textPartFormatSelected || shapeTextEditing
          ? "format"
          : chartPartPrimitiveSelected
            ? "shape"
            : chartSelected
              ? "chart"
              : tableSelected
                ? "table"
                : shapeSelected
                  ? "shape"
                  : dataSelected
                    ? "data"
                    : "home",
      );
    }
  }, [
    activeTab,
    tabs,
    chartSelected,
    tableSelected,
    shapeSelected,
    dataSelected,
    chartPartPrimitiveSelected,
    textPartFormatSelected,
    shapeTextEditing,
  ]);

  useEffect(() => {
    if ((textPartFormatSelected || shapeTextEditing) && isCustomSlide) {
      setActiveTab("format");
    } else if (chartPartPrimitiveSelected && isCustomSlide) {
      setActiveTab("shape");
    } else if (shapeSelected && isCustomSlide) {
      setActiveTab("shape");
    } else if (tableSelected && isCustomSlide) {
      setActiveTab("table");
    } else if (
      shapeChromeSelected &&
      isCustomSlide &&
      !chartSelected &&
      !tableSelected &&
      !textPartFormatSelected
    ) {
      setActiveTab("shape");
    } else if (chartSelected && isCustomSlide && !textPartFormatSelected) {
      setActiveTab("chart");
    } else if (dataSelected && isCustomSlide && !chartSelected && !tableSelected && !shapeSelected) {
      setActiveTab("data");
    }
  }, [
    chartSelected,
    tableSelected,
    shapeSelected,
    shapeChromeSelected,
    chartPartPrimitiveSelected,
    textPartFormatSelected,
    shapeTextEditing,
    dataSelected,
    isCustomSlide,
    editor?.selectedId,
    editor?.selectedChartPart,
    editor?.selectedKpiPart,
    editor?.editingTextId,
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
                disabled={tab.disabledWhenNoSlide ? !slide : false}
                onSelect={() => setActiveTab(tab.id)}
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

      {isRibbonTab(activeTab) ? (
        <div className="td-deck-chrome__ribbon">
          <DeckRibbonShell>
            {activeTab === "home" ? <SlideDeckRibbon {...slideDeck} /> : null}
            {isCustomSlide &&
            (activeTab === "insert" ||
              activeTab === "format" ||
              activeTab === "chart" ||
              activeTab === "table" ||
              activeTab === "shape" ||
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
