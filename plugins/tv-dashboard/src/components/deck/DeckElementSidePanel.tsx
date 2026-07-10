import { ChevronLeft, Database, Layers, MousePointer2 } from "lucide-react";
import { FormatPaneShell } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DataRoutesSidePanel } from "../DataRoutesSidePanel";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ComunicadoElementInspector } from "./ComunicadoElementInspector";
import { ComunicadoLayersPanel } from "./ComunicadoLayersPanel";

type Labels = Record<string, string>;
type SideTab = "element" | "layers" | "data";

const PANEL_TABS = [
  { id: "element" as const, label: "Elemento" },
  { id: "data" as const, label: "Dados" },
  { id: "layers" as const, label: "Camadas" },
];

const PANEL_TITLES: Record<SideTab, string> = {
  element: "Definir elemento",
  data: "Fontes de dados",
  layers: "Camadas",
};

type Props = {
  labels?: Labels;
  /** Dentro do card do palco (não coluna externa do grid). */
  embedded?: boolean;
};

/** Painel lateral estilo PowerPoint — propriedades, dados e camadas. */
export function DeckElementSidePanel({ labels = {}, embedded = true }: Props) {
  const { selectedIds, dataPanelOpen, setDataPanelOpen } = useComunicadoEditor();
  const [open, setOpen] = useState(true);
  const [tab, setTab] = useState<SideTab>("element");

  useEffect(() => {
    if (selectedIds.length > 0) setOpen(true);
  }, [selectedIds]);

  useEffect(() => {
    if (dataPanelOpen) {
      setOpen(true);
      setTab("data");
    }
  }, [dataPanelOpen]);

  const panelTitle = useMemo(() => PANEL_TITLES[tab], [tab]);

  function handleTabChange(next: SideTab) {
    setTab(next);
    if (next === "data") {
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
              onOpenDataSources={() => handleTabChange("data")}
            />
          ) : tab === "data" ? (
            <DataRoutesSidePanel onInserted={() => handleTabChange("element")} />
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
            title="Fontes de dados"
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
