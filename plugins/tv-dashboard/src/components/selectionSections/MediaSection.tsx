import { FolderOpen, Upload } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckPropertySection } from "../deck/DeckPropertySection";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import type { SelectionSectionLayout } from "./types";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/** Biblioteca / upload de mídia (image/video). */
export function MediaSection({
  layout,
  labels = {},
}: {
  layout: SelectionSectionLayout;
  labels?: Record<string, string>;
}) {
  const { selected, uploading, openMediaLibrary, triggerUpload } = useComunicadoEditor();
  if (!selected || (selected.type !== "image" && selected.type !== "video")) return null;

  if (layout === "pane") {
    return (
      <DeckPropertySection title="Mídia" hint={E.uploadMedia} defaultOpen>
        <div className="td-deck-inspector__actions">
          <HintAction hint={E.uploadMedia} ariaLabel="Ajuda: biblioteca de mídia">
            <button
              type="button"
              className="td-btn td-btn--sm"
              onClick={() => openMediaLibrary("block")}
            >
              <FolderOpen size={15} aria-hidden="true" />
              Biblioteca
            </button>
          </HintAction>
          <HintAction hint={E.uploadMedia} ariaLabel="Ajuda: enviar arquivo">
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={uploading}
              onClick={() => triggerUpload("block")}
            >
              <Upload size={15} aria-hidden="true" />
              {uploading ? "Enviando…" : labels.comunicadoUpload ?? "Enviar arquivo"}
            </button>
          </HintAction>
        </div>
      </DeckPropertySection>
    );
  }

  return (
    <DeckRibbonGroup label="Mídia" hint={E.uploadMedia}>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={FolderOpen}
          label="Biblioteca"
          hint={E.uploadMedia}
          onClick={() => openMediaLibrary("block")}
        />
        <DeckRibbonTile
          icon={Upload}
          label={uploading ? "Enviando…" : "Enviar"}
          hint={E.uploadMedia}
          onClick={() => {
            if (!uploading) triggerUpload("block");
          }}
        />
      </div>
    </DeckRibbonGroup>
  );
}
