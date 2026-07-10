import { Database, Layers, MousePointer2, PanelRightClose } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";
import { useEffect, useState } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DataRoutesSidePanel } from "../DataRoutesSidePanel";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ComunicadoElementInspector } from "./ComunicadoElementInspector";
import { ComunicadoLayersPanel } from "./ComunicadoLayersPanel";

type Labels = Record<string, string>;
type SideTab = "element" | "layers" | "data";

type Props = {
  labels?: Labels;
  /** Dentro do card do palco (não coluna externa do grid). */
  embedded?: boolean;
};

/** Painel colapsável à direita do palco — propriedades do elemento selecionado. */
export function DeckElementSidePanel({ labels = {}, embedded = true }: Props) {
  const { selectedIds, dataPanelOpen, setDataPanelOpen } = useComunicadoEditor();
  const [open, setOpen] = useState(false);
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

  const hint = TV_DASHBOARD_HELP_TOOLTIPS.tabs.element;
  const dataHint = TV_DASHBOARD_HELP_TOOLTIPS.tabs.data;

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
      aria-label="Propriedades do elemento"
    >
      <div className="td-deck-side-panel__tab-stack">
        <HintAction hint={hint} ariaLabel="Ajuda: Elemento" placement="left">
          <button
            type="button"
            className={`td-deck-side-panel__tab${tab === "element" && open ? " td-deck-side-panel__tab--active" : ""}`}
            onClick={() => {
              setOpen((value) => (tab === "element" ? !value : true));
              handleTabChange("element");
            }}
            aria-expanded={open && tab === "element"}
            aria-controls="td-deck-element-panel"
          >
            {open && tab === "element" ? (
              <PanelRightClose size={16} aria-hidden="true" />
            ) : (
              <MousePointer2 size={16} aria-hidden="true" />
            )}
            <span className="td-deck-side-panel__tab-label">Elemento</span>
          </button>
        </HintAction>
        <HintAction hint={dataHint} ariaLabel="Ajuda: Dados" placement="left">
          <button
            type="button"
            className={`td-deck-side-panel__tab${tab === "data" && open ? " td-deck-side-panel__tab--active" : ""}`}
            onClick={() => {
              setOpen(true);
              handleTabChange("data");
            }}
            aria-expanded={open && tab === "data"}
            aria-controls="td-deck-element-panel"
          >
            <Database size={16} aria-hidden="true" />
            <span className="td-deck-side-panel__tab-label">Dados</span>
          </button>
        </HintAction>
      </div>
      {open ? (
        <div id="td-deck-element-panel" className="td-deck-side-panel__content">
          <header className="td-deck-side-panel__header">
            <div className="td-deck-side-panel__tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={tab === "element"}
                className={`td-deck-side-panel__tab-btn${tab === "element" ? " td-deck-side-panel__tab-btn--active" : ""}`}
                onClick={() => handleTabChange("element")}
              >
                <MousePointer2 size={14} aria-hidden="true" />
                Elemento
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={tab === "data"}
                className={`td-deck-side-panel__tab-btn${tab === "data" ? " td-deck-side-panel__tab-btn--active" : ""}`}
                onClick={() => handleTabChange("data")}
              >
                <Database size={14} aria-hidden="true" />
                Dados
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={tab === "layers"}
                className={`td-deck-side-panel__tab-btn${tab === "layers" ? " td-deck-side-panel__tab-btn--active" : ""}`}
                onClick={() => handleTabChange("layers")}
              >
                <Layers size={14} aria-hidden="true" />
                Camadas
              </button>
            </div>
          </header>
          {tab === "element" ? (
            <ComunicadoElementInspector labels={labels} placement="side" />
          ) : tab === "data" ? (
            <div className="td-deck-side-panel__data">
              <DataRoutesSidePanel onInserted={() => handleTabChange("element")} />
            </div>
          ) : (
            <div className="td-deck-side-panel__layers">
              <ComunicadoLayersPanel />
            </div>
          )}
        </div>
      ) : null}
    </aside>
  );
}
