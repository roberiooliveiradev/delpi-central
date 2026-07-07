import { Upload } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "./DeckField";
import { DeckPropertySection } from "./DeckPropertySection";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

type Labels = Record<string, string>;

export function ComunicadoSlideBackgroundPanel({ labels = {} }: { labels?: Labels }) {
  const { uploading, background, triggerUpload, setBackgroundColor } = useComunicadoEditor();

  return (
    <DeckPropertySection title={labels.comunicadoBackground ?? "Fundo do slide"} hint={E.backgroundColor}>
      <DeckField id="td-bg-color" label="Cor" hint={E.backgroundColor}>
        <input
          id="td-bg-color"
          type="color"
          className="td-deck-color-input"
          value={background?.type === "color" ? background.value : "#0f172a"}
          onChange={(e) => setBackgroundColor(e.target.value)}
        />
      </DeckField>
      <HintAction hint={E.uploadBackground} ariaLabel="Ajuda: imagem de fundo">
        <button
          type="button"
          className="td-btn td-btn--sm"
          disabled={uploading}
          onClick={() => triggerUpload("background")}
        >
          <Upload size={15} aria-hidden="true" />
          {labels.comunicadoUpload ?? "Enviar imagem de fundo"}
        </button>
      </HintAction>
    </DeckPropertySection>
  );
}
