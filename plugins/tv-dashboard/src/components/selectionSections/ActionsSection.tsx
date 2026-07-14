import { Trash2 } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckActionRow } from "../deck/DeckActionRow";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/**
 * Ações do painel — só Remover (camada/duplicar ficam em Organizar).
 */
export function ActionsSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selectedIds, removeSelected } = useComunicadoEditor();
  if (layout === "ribbon") return null;
  if (selectedIds.length === 0) return null;

  return (
    <SelectionPaneSection title="Ações" hint={E.remove} defaultOpen={false}>
      <DeckActionRow>
        <HintAction hint={E.remove} ariaLabel="Ajuda: remover">
          <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={removeSelected}>
            <Trash2 size={15} aria-hidden="true" />
            Remover
          </button>
        </HintAction>
      </DeckActionRow>
    </SelectionPaneSection>
  );
}
