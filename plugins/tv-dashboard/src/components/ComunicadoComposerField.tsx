import { ComunicadoComposerCanvas } from "./ComunicadoComposer";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import { ComunicadoEmbeddedEditorChrome } from "./ComunicadoEmbeddedEditorChrome";
import { DeckElementSidePanel } from "./deck";

type Props = {
  playlistId: string;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  labels?: Record<string, string>;
};

export function ComunicadoComposerField({ playlistId, value, onChange, labels = {} }: Props) {
  return (
    <ComunicadoEditorProvider playlistId={playlistId} value={value} onChange={onChange}>
      <div className="td-composer-embedded">
        <ComunicadoEmbeddedEditorChrome labels={labels} />
        <div className="td-composer-embedded__stage">
          <div className="td-deck-stage__editor">
            <ComunicadoComposerCanvas />
          </div>
          <DeckElementSidePanel labels={labels} />
        </div>
      </div>
    </ComunicadoEditorProvider>
  );
}
