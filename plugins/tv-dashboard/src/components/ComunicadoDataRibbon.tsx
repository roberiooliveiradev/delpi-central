import { useComunicadoEditor } from "./comunicadoEditorContext";
import { SelectedDataSidePanel } from "./SelectedDataSidePanel";

/**
 * Aba Dados na top bar — mesmos controles do painel lateral Dados
 * em layout full-width com grade de campos.
 */
export function ComunicadoDataRibbon() {
  const { setSelectionPanelTab, setDataPanelIntent } = useComunicadoEditor();

  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--inspector">
      <SelectedDataSidePanel
        layout="ribbon"
        onInserted={() => {
          setDataPanelIntent("binding");
          setSelectionPanelTab("element");
        }}
        onOpenCatalog={() => setDataPanelIntent("catalog")}
      />
    </div>
  );
}
