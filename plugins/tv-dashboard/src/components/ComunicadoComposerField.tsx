import { ComunicadoComposerCanvas } from "./ComunicadoComposer";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import { ComunicadoEditorRibbon } from "./ComunicadoEditorRibbon";
import { ComunicadoElementInspector, DeckRibbonShell } from "./deck";

type Props = {
  playlistId: string;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  labels?: Record<string, string>;
};

export function ComunicadoComposerField({ playlistId, value, onChange, labels = {} }: Props) {
  return (
    <ComunicadoEditorProvider playlistId={playlistId} value={value} onChange={onChange}>
      <DeckRibbonShell embedded>
        <ComunicadoEditorRibbon labels={labels} />
      </DeckRibbonShell>
      <div className="td-deck-tabs td-deck-tabs--embedded">
        <ComunicadoElementInspector labels={labels} />
      </div>
      <ComunicadoComposerCanvas />
    </ComunicadoEditorProvider>
  );
}

export { ComunicadoComposerCanvas, ComunicadoElementInspector };
