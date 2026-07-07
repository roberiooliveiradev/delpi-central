import { ComunicadoComposerCanvas, ComunicadoElementPanel } from "./ComunicadoComposer";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import { ComunicadoEditorRibbon } from "./ComunicadoEditorRibbon";

type Props = {
  playlistId: string;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  labels?: Record<string, string>;
};

export function ComunicadoComposerField({ playlistId, value, onChange, labels = {} }: Props) {
  return (
    <ComunicadoEditorProvider playlistId={playlistId} value={value} onChange={onChange}>
      <div className="td-deck-ribbon td-deck-ribbon--embedded">
        <ComunicadoEditorRibbon labels={labels} />
      </div>
      <div className="td-deck-tabs td-deck-tabs--embedded">
        <ComunicadoElementPanel labels={labels} />
      </div>
      <ComunicadoComposerCanvas />
    </ComunicadoEditorProvider>
  );
}

export { ComunicadoComposerCanvas, ComunicadoElementPanel };
