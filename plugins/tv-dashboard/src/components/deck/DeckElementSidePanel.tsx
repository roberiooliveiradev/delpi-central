import { Layers, MousePointer2, PanelRightClose } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui";
import { useEffect, useState } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ComunicadoElementInspector } from "./ComunicadoElementInspector";
import { ComunicadoLayersPanel } from "./ComunicadoLayersPanel";

type Labels = Record<string, string>;
type SideTab = "element" | "layers";

type Props = {
  labels?: Labels;
  /** Dentro do card do palco (não coluna externa do grid). */
  embedded?: boolean;
};

/** Painel colapsável à direita do palco — propriedades do elemento selecionado. */
export function DeckElementSidePanel({ labels = {}, embedded = true }: Props) {
  const { selectedIds } = useComunicadoEditor();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<SideTab>("element");

  useEffect(() => {
    if (selectedIds.length > 0) setOpen(true);
  }, [selectedIds]);

  const hint = TV_DASHBOARD_HELP_TOOLTIPS.tabs.element;

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
      <HintAction hint={hint} ariaLabel="Ajuda: Elemento" placement="left">
        <button
          type="button"
          className="td-deck-side-panel__tab"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-controls="td-deck-element-panel"
        >
          {open ? <PanelRightClose size={16} aria-hidden="true" /> : <MousePointer2 size={16} aria-hidden="true" />}
          <span className="td-deck-side-panel__tab-label">Elemento</span>
        </button>
      </HintAction>
      {open ? (
        <div id="td-deck-element-panel" className="td-deck-side-panel__content">
          <header className="td-deck-side-panel__header">
            <div className="td-deck-side-panel__tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={tab === "element"}
                className={`td-deck-side-panel__tab-btn${tab === "element" ? " td-deck-side-panel__tab-btn--active" : ""}`}
                onClick={() => setTab("element")}
              >
                <MousePointer2 size={14} aria-hidden="true" />
                Elemento
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={tab === "layers"}
                className={`td-deck-side-panel__tab-btn${tab === "layers" ? " td-deck-side-panel__tab-btn--active" : ""}`}
                onClick={() => setTab("layers")}
              >
                <Layers size={14} aria-hidden="true" />
                Camadas
              </button>
            </div>
          </header>
          {tab === "element" ? (
            <ComunicadoElementInspector labels={labels} placement="side" />
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
