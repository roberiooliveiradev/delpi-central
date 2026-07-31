import { ComunicadoComposerCanvas } from "./ComunicadoComposer";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import { ComunicadoEmbeddedEditorChrome } from "./ComunicadoEmbeddedEditorChrome";
import { DataCatalogModalHost } from "./DataCatalogModalHost";
import { DeckElementSidePanel } from "./deck";

type Props = {
  playlistId: string;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  labels?: Record<string, string>;
};

/**
 * Compositor sem filmstrip — mesmo contrato de palco + aside-slot do DeckWorkspace
 * (painel Seleção não pode usar width:100% fora do trilho).
 */
export function ComunicadoComposerField({ playlistId, value, onChange, labels = {} }: Props) {
  return (
    <ComunicadoEditorProvider playlistId={playlistId} value={value} onChange={onChange}>
      <div className="td-composer-embedded">
        <ComunicadoEmbeddedEditorChrome labels={labels} />
        <main className="td-deck-stage td-composer-embedded__stage" aria-label="Palco do template">
          <div className="td-deck-stage__inner">
            <div className="td-deck-stage__main">
              <div className="td-deck-stage__editor">
                <ComunicadoComposerCanvas />
              </div>
            </div>
            <div className="td-deck-stage__aside-slot">
              <div className="td-deck-right-stack">
                <DeckElementSidePanel labels={labels} />
              </div>
            </div>
          </div>
        </main>
        <DataCatalogModalHost />
      </div>
    </ComunicadoEditorProvider>
  );
}
