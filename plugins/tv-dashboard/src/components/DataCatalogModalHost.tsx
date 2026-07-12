import type { BranchScope } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataRoutesSidePanel } from "./DataRoutesSidePanel";
import { Modal } from "./ui/Modal";

type Props = {
  branchScope?: BranchScope | null;
};

/**
 * Catálogo de fontes em modal — usado pela top bar (Inserir / Dados).
 * O painel lateral continua com listagem inline quando a aba Dados está vazia.
 */
export function DataCatalogModalHost({ branchScope = null }: Props) {
  const { dataCatalogModalOpen, setDataCatalogModalOpen, setDataPanelIntent } =
    useComunicadoEditor();

  return (
    <Modal
      open={dataCatalogModalOpen}
      title="Fontes de dados"
      onClose={() => setDataCatalogModalOpen(false)}
      className="td-modal--wide td-modal--data-catalog"
    >
      <DataRoutesSidePanel
        layout="pane"
        branchScope={branchScope}
        onInserted={() => {
          setDataCatalogModalOpen(false);
          setDataPanelIntent("binding");
        }}
      />
    </Modal>
  );
}
