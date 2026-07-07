import { ComunicadoComposer } from "./ComunicadoComposer";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import { ComunicadoEditorRibbon } from "./ComunicadoEditorRibbon";

type Props = {
  playlistId: string;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  labels?: Record<string, string>;
  showRibbon?: boolean;
};

export function ComunicadoComposerField({
  playlistId,
  value,
  onChange,
  labels = {},
  showRibbon = true,
}: Props) {
  return (
    <ComunicadoEditorProvider playlistId={playlistId} value={value} onChange={onChange}>
      {showRibbon ? (
        <div className="td-deck-ribbon td-deck-ribbon--embedded">
          <ComunicadoEditorRibbon labels={labels} />
        </div>
      ) : null}
      <ComunicadoComposer labels={labels} />
    </ComunicadoEditorProvider>
  );
}
