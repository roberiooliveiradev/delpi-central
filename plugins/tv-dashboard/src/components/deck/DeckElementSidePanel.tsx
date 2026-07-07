import { MousePointer2, PanelRightClose } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui";
import { useEffect, useState } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ComunicadoElementInspector } from "./ComunicadoElementInspector";

type Labels = Record<string, string>;

/** Painel colapsável à direita do palco — propriedades do elemento selecionado. */
export function DeckElementSidePanel({ labels = {} }: { labels?: Labels }) {
  const { selectedId } = useComunicadoEditor();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (selectedId) setOpen(true);
  }, [selectedId]);

  const hint = TV_DASHBOARD_HELP_TOOLTIPS.tabs.element;

  return (
    <aside
      className={["td-deck-side-panel", open ? "td-deck-side-panel--open" : "td-deck-side-panel--collapsed"]
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
            <h3 className="td-deck-side-panel__title">Elemento</h3>
          </header>
          <ComunicadoElementInspector labels={labels} placement="side" />
        </div>
      ) : null}
    </aside>
  );
}
