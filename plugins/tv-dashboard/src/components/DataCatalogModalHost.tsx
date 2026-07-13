import type { BranchScope } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataRoutesSidePanel } from "./DataRoutesSidePanel";
import { Modal } from "./ui/Modal";

type Props = {
  branchScope?: BranchScope | null;
};

/**
 * Catálogo de fontes em modal — Inserir (top bar) ou Trocar rota (inspetor Dados).
 * O painel lateral continua com listagem inline quando a aba Dados está vazia.
 */
export function DataCatalogModalHost({ branchScope = null }: Props) {
  const {
    dataCatalogModalOpen,
    setDataCatalogModalOpen,
    dataCatalogMode,
    setDataCatalogMode,
    setDataPanelIntent,
  } = useComunicadoEditor();

  function closeCatalog() {
    setDataCatalogModalOpen(false);
    setDataCatalogMode("insert");
  }

  return (
    <Modal
      open={dataCatalogModalOpen}
      title={dataCatalogMode === "replace" ? "Trocar fonte de dados" : "Fontes de dados"}
      onClose={closeCatalog}
      className="td-modal--wide td-modal--data-catalog"
    >
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
    </Modal>
  );
}
