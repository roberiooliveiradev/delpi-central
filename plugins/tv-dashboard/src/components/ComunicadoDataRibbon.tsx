import { SelectedDataSidePanel } from "./SelectedDataSidePanel";
import { useComunicadoEditor } from "./comunicadoEditorContext";

/**
 * Aba Dados na top bar — mesmos controles do painel lateral Dados
 * em layout full-width com grade de campos.
 */
export function ComunicadoDataRibbon() {
  const { setSelectionPanelTab } = useComunicadoEditor();

  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--inspector">
      <SelectedDataSidePanel
        layout="ribbon"
        onInserted={() => setSelectionPanelTab("element")}
        onOpenCatalog={() => setSelectionPanelTab("data")}
      />
    </div>
  );
}
