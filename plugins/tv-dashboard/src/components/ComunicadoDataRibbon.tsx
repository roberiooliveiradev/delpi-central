import { SelectedDataSidePanel } from "./SelectedDataSidePanel";
import { useComunicadoEditor } from "./comunicadoEditorContext";

/**
 * Aba Dados na top bar — mesmos controles do painel lateral Dados
 * (vínculo / catálogo), em layout compacto horizontal.
 */
export function ComunicadoDataRibbon() {
  const { setSelectionPanelTab } = useComunicadoEditor();

  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--inspector">
      <div className="td-deck-ribbon__inspector">
        <SelectedDataSidePanel
          onInserted={() => setSelectionPanelTab("element")}
          onOpenCatalog={() => setSelectionPanelTab("data")}
        />
      </div>
    </div>
  );
}
