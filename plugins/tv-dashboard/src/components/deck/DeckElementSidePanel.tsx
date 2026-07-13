import { ChevronLeft, Database, Layers, MousePointer2 } from "lucide-react";
import { FormatPaneShell } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, type CSSProperties } from "react";
import { isDataBoundEditorBlockType } from "@delpi/tv-dashboard-presentation";

import type { BranchScope } from "../../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useDeckSidePanelLayout } from "../../hooks/useDeckSidePanelLayout";
import type { SelectionPanelTab } from "../comunicadoEditorContextCore";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { SelectedDataSidePanel } from "../SelectedDataSidePanel";
import { resolveSelectedDataContext } from "../../utils/selectedDataContext";
import { ComunicadoElementInspector } from "./ComunicadoElementInspector";
import { ComunicadoLayersPanel } from "./ComunicadoLayersPanel";

type Labels = Record<string, string>;

const T = TV_DASHBOARD_HELP_TOOLTIPS.tabs;

const PANEL_TABS = [
  { id: "element" as const, label: "Elemento", hint: T.element },
  { id: "data" as const, label: "Dados", hint: T.data },
  { id: "layers" as const, label: "Camadas", hint: T.layers },
];

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
  } = useComunicadoEditor();
  const { collapsed, setCollapsed, startResize, panelWidthPx, limits, width } =
    useDeckSidePanelLayout("inspector", { growDirection: "west" });
  const open = !collapsed;

  const dataContext = useMemo(
    () => resolveSelectedDataContext(blocks, selectedIds),
    [blocks, selectedIds],
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

  const tab = selectionPanelTab;

  const panelTitle = useMemo(() => {
    if (tab !== "data") {
      return tab === "element" ? "Definir elemento" : "Camadas";
    }
    if (dataPanelIntent === "catalog" || dataContext.kind === "none") {
      return "Fontes de dados";
    }
    return "Dados do elemento";
  }, [tab, dataPanelIntent, dataContext.kind]);

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
            tabs={PANEL_TABS}
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
