import { useComunicadoEditor } from "./comunicadoEditorContext";
import { SelectedDataSidePanel } from "./SelectedDataSidePanel";

/**
 * Aba Dados na top bar — configuração da fonte selecionada;
 * catálogo abre em modal (não na faixa nem no painel lateral).
 */
export function ComunicadoDataRibbon() {
  const { setSelectionPanelTab, setDataPanelIntent, openDataCatalog } = useComunicadoEditor();

  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--inspector">
      <SelectedDataSidePanel
        layout="ribbon"
        onInserted={() => {
          setDataPanelIntent("binding");
          setSelectionPanelTab("element");
        }}
        onOpenCatalog={() => openDataCatalog()}
      />
    </div>
  );
}
