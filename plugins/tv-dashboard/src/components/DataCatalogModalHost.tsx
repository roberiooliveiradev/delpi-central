import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import { X } from "lucide-react";
import { useRef } from "react";

import { DATA_BUILDER_CHAT_CONTENT } from "../content/dataBuilderChatContent";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataBuilderChatPanel } from "./DataBuilderChatPanel";

/**
 * Assistente conversacional de dados — Inserir (ribbon) ou Trocar rota (inspetor).
 */
export function DataCatalogModalHost({ branchScope: _branchScope = null }: { branchScope?: unknown }) {
  const {
    dataCatalogModalOpen,
    setDataCatalogModalOpen,
    dataCatalogMode,
    setDataCatalogMode,
    dataCatalogAnchor,
    setDataCatalogAnchor,
    setDataPanelIntent,
  } = useComunicadoEditor();

  const panelRef = useRef<HTMLDivElement>(null);
  const fallbackAnchorRef = useRef<HTMLDivElement>(null);
  const resolvedAnchorRef = useRef<HTMLElement | null>(null);
  // Sync no render — o positioning do portal lê o ref no layout effect.
  resolvedAnchorRef.current = dataCatalogAnchor ?? fallbackAnchorRef.current;

  function closeCatalog() {
    setDataCatalogModalOpen(false);
    setDataCatalogMode("insert");
    setDataCatalogAnchor(null);
  }

  const title =
    dataCatalogMode === "replace"
      ? DATA_BUILDER_CHAT_CONTENT.titleReplace
      : DATA_BUILDER_CHAT_CONTENT.title;

  return (
    <>
      <div
        ref={fallbackAnchorRef}
        className="td-data-catalog-popover__fallback-anchor"
        aria-hidden="true"
      />
      {dataCatalogModalOpen ? (
        <AnchoredPanelPortal
          open
          anchorRef={resolvedAnchorRef}
          panelRef={panelRef}
          variant="bare"
          preferredPlacement="bottom"
          gap={8}
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-data-catalog-popover td-data-catalog-popover--builder"
          role="dialog"
          aria-label={title}
          density="compact"
          onDismiss={closeCatalog}
        >
          <div className="td-data-catalog-popover__chrome">
            <header className="td-data-catalog-popover__header">
              <h2 className="td-data-catalog-popover__title">{title}</h2>
              <button
                type="button"
                className="td-data-catalog-popover__close"
                aria-label="Fechar assistente"
                onClick={closeCatalog}
              >
                <X size={16} aria-hidden="true" />
              </button>
            </header>
            <div className="td-data-catalog-popover__body">
              <DataBuilderChatPanel
                mode={dataCatalogMode}
                onInserted={() => {
                  closeCatalog();
                  setDataPanelIntent("binding");
                }}
              />
            </div>
          </div>
        </AnchoredPanelPortal>
      ) : null}
    </>
  );
}
