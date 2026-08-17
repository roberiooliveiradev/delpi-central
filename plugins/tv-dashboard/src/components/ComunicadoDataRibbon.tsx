import { useEffect } from "react";
import { isDataBoundEditorBlockType } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import { SelectedDataSidePanel } from "./SelectedDataSidePanel";

/**
 * Aba Dados na top bar — toolbar compacta; inspector completo no painel lateral.
 * Catálogo abre em popover ancorado.
 */
export function ComunicadoDataRibbon() {
  const {
    selected,
    setSelectionPanelTab,
    setDataPanelIntent,
    setDataPanelOpen,
    openDataCatalog,
  } = useComunicadoEditor();

  const selectedId = selected?.id ?? "";
  const selectedType = selected?.type;
  useEffect(() => {
    setSelectionPanelTab("data");
    setDataPanelOpen(true);
    const preferCatalog = !selectedType || !isDataBoundEditorBlockType(selectedType);
    setDataPanelIntent(preferCatalog ? "catalog" : "binding");
    // selected object identity muda a cada preview/hydrate — só id/tipo importam.
  }, [selectedId, selectedType, setDataPanelIntent, setDataPanelOpen, setSelectionPanelTab]);

  return (
    <DeckRibbonGroups className="td-deck-ribbon__groups--inspector" overflowEnabled={false}>
      <SelectedDataSidePanel
        layout="ribbon"
        onInserted={() => {
          setDataPanelIntent("binding");
          setSelectionPanelTab("element");
        }}
        onOpenCatalog={openDataCatalog}
      />
    </DeckRibbonGroups>
  );
}
