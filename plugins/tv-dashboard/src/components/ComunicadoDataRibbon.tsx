import { useComunicadoEditor } from "./comunicadoEditorContext";
import { SelectedDataSidePanel } from "./SelectedDataSidePanel";

/**
 * Aba Dados na top bar — mesmos controles do painel lateral Dados
 * em layout full-width com grade de campos.
 */
export function ComunicadoDataRibbon() {
  const {
    setSelectionPanelTab,
    setDataPanelIntent,
    setDataPanelOpen,
  } = useComunicadoEditor();

  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--inspector">
      <SelectedDataSidePanel
        layout="ribbon"
        onInserted={() => {
          setDataPanelIntent("binding");
          setSelectionPanelTab("element");
        }}
        onOpenCatalog={() => {
          // Catálogo completo não cabe na ribbon (max ~120px) — abre no painel lateral.
          setDataPanelIntent("catalog");
          setDataPanelOpen(true);
          setSelectionPanelTab("data");
        }}
      />
    </div>
  );
}
