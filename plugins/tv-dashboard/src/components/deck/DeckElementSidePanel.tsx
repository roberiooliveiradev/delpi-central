import { ChevronLeft, Database, Layers, MousePointer2 } from "lucide-react";
import { FormatPaneShell } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";
import { isDataBoundEditorBlockType } from "@delpi/tv-dashboard-presentation";

import type { BranchScope } from "../../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { SelectedDataSidePanel } from "../SelectedDataSidePanel";
import { resolveSelectedDataContext } from "../../utils/selectedDataContext";
import { ComunicadoElementInspector } from "./ComunicadoElementInspector";
import { ComunicadoLayersPanel } from "./ComunicadoLayersPanel";

type Labels = Record<string, string>;
type SideTab = "element" | "layers" | "data";

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

/** Painel lateral estilo PowerPoint — propriedades, dados e camadas. */
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
  } = useComunicadoEditor();
  const [open, setOpen] = useState(true);
  const [tab, setTab] = useState<SideTab>("element");

  const dataContext = useMemo(
    () => resolveSelectedDataContext(blocks, selectedIds),
    [blocks, selectedIds],
  );

  useEffect(() => {
    if (selectedIds.length > 0) setOpen(true);
  }, [selectedIds]);

  useEffect(() => {
    if (dataPanelOpen) {
      setOpen(true);
      setTab("data");
    }
  }, [dataPanelOpen]);

  const panelTitle = useMemo(() => {
    if (tab !== "data") {
      return tab === "element" ? "Definir elemento" : "Camadas";
    }
    if (dataPanelIntent === "catalog" || dataContext.kind === "none") {
      return "Fontes de dados";
    }
    return "Dados do elemento";
  }, [tab, dataPanelIntent, dataContext.kind]);

  function handleTabChange(next: SideTab) {
    setTab(next);
    if (next === "data") {
      const preferCatalog =
        !selected || !isDataBoundEditorBlockType(selected.type);
      setDataPanelIntent(preferCatalog ? "catalog" : "binding");
      setDataPanelOpen(true);
    } else {
      setDataPanelOpen(false);
    }
  }

  return (
    <aside
      className={[
        "td-deck-side-panel",
        embedded ? "td-deck-side-panel--stage" : null,
        open ? "td-deck-side-panel--open" : "td-deck-side-panel--collapsed",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Painel de formatação"
    >
      {open ? (
        <FormatPaneShell
          className="td-deck-side-panel__pane"
          title={panelTitle}
          closeLabel="Fechar painel de formatação"
          onClose={() => setOpen(false)}
          tabs={PANEL_TABS}
          activeTabId={tab}
          onTabChange={(id) => handleTabChange(id as SideTab)}
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
      ) : (
        <div className="td-deck-side-panel__collapsed-rail">
          <button
            type="button"
            className="td-deck-side-panel__reopen"
            onClick={() => setOpen(true)}
            aria-label="Abrir painel de formatação"
            title="Abrir painel"
          >
            <ChevronLeft size={18} aria-hidden="true" />
          </button>
          <button
            type="button"
            className={`td-deck-side-panel__rail-btn${tab === "element" ? " td-deck-side-panel__rail-btn--active" : ""}`}
            onClick={() => {
              setOpen(true);
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
              setOpen(true);
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
              setOpen(true);
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
