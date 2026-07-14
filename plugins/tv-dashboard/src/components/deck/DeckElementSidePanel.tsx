import { ChevronLeft, Database, Layers, MousePointer2 } from "lucide-react";
import { FormatPaneShell } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useRef, type CSSProperties } from "react";
import { isDataBoundEditorBlockType } from "@delpi/tv-dashboard-presentation";

import type { BranchScope } from "../../api/tvDashboardApi";
import { useDeckSidePanelLayout } from "../../hooks/useDeckSidePanelLayout";
import type { SelectionPanelTab } from "../comunicadoEditorContextCore";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { SelectedDataSidePanel } from "../SelectedDataSidePanel";
import { resolveSelectedDataContext } from "../../utils/selectedDataContext";
import { resolveTableFormatPaneTitle } from "../../utils/resolveTableFormatPaneTitle";
import { ComunicadoElementInspector } from "./ComunicadoElementInspector";
import { ComunicadoLayersPanel } from "./ComunicadoLayersPanel";
import { resolveSelectionPanelTabs } from "./deckRibbonTabMeta";

type Labels = Record<string, string>;

type Props = {
  labels?: Labels;
  /** Dentro do card do palco (não coluna externa do grid). */
  embedded?: boolean;
  branchScope?: BranchScope | null;
};

/** Painel lateral — Elemento / Dados / Camadas (espelhados na top bar). */
export function DeckElementSidePanel({ labels = {}, embedded = true, branchScope = null }: Props) {
  const {
    selected,
    selectedIds,
    blocks,
    dataPanelOpen,
    setDataPanelOpen,
    dataPanelIntent,
    setDataPanelIntent,
    openDataCatalog,
    selectionPanelTab,
    setSelectionPanelTab,
    requestRibbonTab,
    selectedTablePart,
  } = useComunicadoEditor();
  const { collapsed, setCollapsed, startResize, panelWidthPx, limits, width } =
    useDeckSidePanelLayout("inspector", { growDirection: "west" });
  const open = !collapsed;
  const prevSelectionCount = useRef(selectedIds.length);

  const dataContext = useMemo(
    () => resolveSelectedDataContext(blocks, selectedIds),
    [blocks, selectedIds],
  );

  const hasSelection = selectedIds.length > 0;
  const hasDataBoundSelection = Boolean(
    selected && isDataBoundEditorBlockType(selected.type),
  );
  const showDataTab = dataPanelOpen || hasDataBoundSelection;
  const panelTabs = useMemo(
    () => resolveSelectionPanelTabs({ hasSelection, showDataTab }),
    [hasSelection, showDataTab],
  );

  useEffect(() => {
    if (selectedIds.length > 0) setCollapsed(false);
  }, [selectedIds, setCollapsed]);

  useEffect(() => {
    if (dataPanelOpen) {
      setCollapsed(false);
      setSelectionPanelTab("data");
    }
  }, [dataPanelOpen, setCollapsed, setSelectionPanelTab]);

  /** Auto-aba: seleção → Elemento; desseleção → Camadas. */
  useEffect(() => {
    const prev = prevSelectionCount.current;
    const next = selectedIds.length;
    prevSelectionCount.current = next;
    if (next > 0 && prev === 0) {
      setSelectionPanelTab("element");
      requestRibbonTab("element");
      return;
    }
    if (next === 0 && prev > 0) {
      setSelectionPanelTab("layers");
      setDataPanelOpen(false);
    }
  }, [selectedIds.length, requestRibbonTab, setDataPanelOpen, setSelectionPanelTab]);

  /** Se a aba ativa sumiu do set visível, cair para a primeira disponível. */
  useEffect(() => {
    if (!panelTabs.some((t) => t.id === selectionPanelTab)) {
      const fallback = panelTabs[panelTabs.length - 1]?.id ?? "layers";
      setSelectionPanelTab(fallback);
    }
  }, [panelTabs, selectionPanelTab, setSelectionPanelTab]);

  const tab = selectionPanelTab;

  const panelTitle = useMemo(() => {
    if (tab === "layers") return "Camadas";
    if (tab === "data") {
      if (dataPanelIntent === "catalog" || dataContext.kind === "none") {
        return "Fontes de dados";
      }
      return "Dados do elemento";
    }
    if (selected?.type === "table_view") return resolveTableFormatPaneTitle(selectedTablePart);
    if (selected?.type === "chart_view") return "Formatar Gráfico";
    if (
      selected?.type === "shape" ||
      selected?.type === "text" ||
      selected?.type === "heading"
    ) {
      return "Definir Forma";
    }
    if (selected?.type === "kpi_view") return "Formatar KPI";
    return "Definir elemento";
  }, [tab, dataPanelIntent, dataContext.kind, selected?.type, selectedTablePart]);

  function handleTabChange(next: SelectionPanelTab) {
    setSelectionPanelTab(next);
    requestRibbonTab(next);
    if (next === "data") {
      const preferCatalog =
        !selected || !isDataBoundEditorBlockType(selected.type);
      setDataPanelIntent(preferCatalog ? "catalog" : "binding");
      setDataPanelOpen(true);
    } else {
      setDataPanelOpen(false);
    }
  }

  const panelStyle = {
    "--td-side-panel-width": `${open ? width : panelWidthPx}px`,
  } as CSSProperties;

  const railShowsElement = panelTabs.some((t) => t.id === "element");
  const railShowsData = panelTabs.some((t) => t.id === "data");

  return (
    <aside
      className={[
        "td-deck-side-panel",
        embedded ? "td-deck-side-panel--stage" : null,
        open ? "td-deck-side-panel--open" : "td-deck-side-panel--collapsed",
      ]
        .filter(Boolean)
        .join(" ")}
      style={panelStyle}
      aria-label="Painel de formatação"
    >
      {open ? (
        <>
          <div
            className="td-deck-panel-resize td-deck-panel-resize--west"
            role="separator"
            aria-orientation="vertical"
            aria-label="Redimensionar painel de formatação"
            aria-valuenow={width}
            aria-valuemin={limits.minWidth}
            aria-valuemax={limits.maxWidth}
            onPointerDown={startResize}
          />
          <FormatPaneShell
            className="td-deck-side-panel__pane"
            title={panelTitle}
            closeLabel="Recolher painel de formatação"
            onClose={() => setCollapsed(true)}
            tabs={panelTabs}
            activeTabId={tab}
            onTabChange={(id) => handleTabChange(id as SelectionPanelTab)}
            bodyClassName="td-deck-side-panel__pane-body"
          >
            {tab === "element" ? (
              <ComunicadoElementInspector
                labels={labels}
                placement="side"
                branchScope={branchScope}
                onOpenDataSources={() => openDataCatalog()}
              />
            ) : tab === "data" ? (
              <SelectedDataSidePanel
                branchScope={branchScope}
                onInserted={() => handleTabChange("element")}
                onOpenCatalog={() => openDataCatalog()}
              />
            ) : (
              <ComunicadoLayersPanel />
            )}
          </FormatPaneShell>
        </>
      ) : (
        <div className="td-deck-side-panel__collapsed-rail">
          <button
            type="button"
            className="td-deck-side-panel__reopen"
            onClick={() => setCollapsed(false)}
            aria-label="Expandir painel de formatação"
            title="Expandir painel"
          >
            <ChevronLeft size={18} aria-hidden="true" />
          </button>
          {railShowsElement ? (
            <button
              type="button"
              className={`td-deck-side-panel__rail-btn${tab === "element" ? " td-deck-side-panel__rail-btn--active" : ""}`}
              onClick={() => {
                setCollapsed(false);
                handleTabChange("element");
              }}
              aria-label="Elemento"
              title="Definir elemento"
            >
              <MousePointer2 size={16} aria-hidden="true" />
            </button>
          ) : null}
          {railShowsData ? (
            <button
              type="button"
              className={`td-deck-side-panel__rail-btn${tab === "data" ? " td-deck-side-panel__rail-btn--active" : ""}`}
              onClick={() => {
                setCollapsed(false);
                handleTabChange("data");
              }}
              aria-label="Dados"
              title="Dados"
            >
              <Database size={16} aria-hidden="true" />
            </button>
          ) : null}
          <button
            type="button"
            className={`td-deck-side-panel__rail-btn${tab === "layers" ? " td-deck-side-panel__rail-btn--active" : ""}`}
            onClick={() => {
              setCollapsed(false);
              handleTabChange("layers");
            }}
            aria-label="Camadas"
            title="Camadas"
          >
            <Layers size={16} aria-hidden="true" />
          </button>
        </div>
      )}
    </aside>
  );
}
