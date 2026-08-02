import { DATA_BUILDER_CHAT_CONTENT } from "../content/dataBuilderChatContent";
import type { BranchScope } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataBuilderChatPanel } from "./DataBuilderChatPanel";
import { HostContainedModal } from "./ui/Modal";

/**
 * Assistente de dados — workbench host-contained (Inserir / Trocar rota).
 * Usa `HostContainedModal` do plugin-ui (não popover ancorado).
 */
export function DataCatalogModalHost({ branchScope = null }: { branchScope?: BranchScope | null }) {
  const {
    dataCatalogModalOpen,
    setDataCatalogModalOpen,
    dataCatalogMode,
    setDataCatalogMode,
    setDataCatalogAnchor,
    setDataPanelIntent,
  } = useComunicadoEditor();

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
    <HostContainedModal
      open={dataCatalogModalOpen}
      title={title}
      onClose={closeCatalog}
      closeAriaLabel="Fechar assistente"
      className="td-modal--data-catalog"
    >
      <DataBuilderChatPanel
        mode={dataCatalogMode}
        branchScope={branchScope}
        onInserted={() => {
          closeCatalog();
          setDataPanelIntent("binding");
        }}
      />
    </HostContainedModal>
  );
}
