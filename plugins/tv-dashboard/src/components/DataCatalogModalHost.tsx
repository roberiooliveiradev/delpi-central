import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import { X } from "lucide-react";
import { useRef } from "react";

import type { BranchScope } from "../api/tvDashboardApi";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataRoutesSidePanel } from "./DataRoutesSidePanel";

type Props = {
  branchScope?: BranchScope | null;
};

/**
 * Catálogo de fontes em popover ancorado — Inserir (ribbon) ou Trocar rota (inspetor).
 * O painel lateral continua com listagem inline quando a aba Dados está vazia.
 */
export function DataCatalogModalHost({ branchScope = null }: Props) {
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

  const title = dataCatalogMode === "replace" ? "Trocar fonte de dados" : "Fontes de dados";

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
          className="td-data-catalog-popover"
          role="dialog"
          aria-label={title}
          onDismiss={closeCatalog}
        >
          <div className="td-data-catalog-popover__chrome">
            <header className="td-data-catalog-popover__header">
              <h2 className="td-data-catalog-popover__title">{title}</h2>
              <button
                type="button"
                className="td-data-catalog-popover__close"
                aria-label="Fechar catálogo"
                onClick={closeCatalog}
              >
                <X size={16} aria-hidden="true" />
              </button>
            </header>
            <div className="td-data-catalog-popover__body">
              <DataRoutesSidePanel
                layout="pane"
                hideHeading
                mode={dataCatalogMode}
                branchScope={branchScope}
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
