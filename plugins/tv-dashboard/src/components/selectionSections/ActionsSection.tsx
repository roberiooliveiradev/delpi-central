import { ArrowDown, ArrowUp, Trash2 } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckActionRow } from "../deck/DeckActionRow";
import { DeckPropertySection } from "../deck/DeckPropertySection";
import type { SelectionSectionLayout } from "./types";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/**
 * Ações de camada / remover — painel (ribbon omite; Organize cobre camada na faixa).
 */
export function ActionsSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selectedIds, moveLayer, removeSelected } = useComunicadoEditor();
  if (layout === "ribbon") return null;
  if (selectedIds.length === 0) return null;

  const multiSelect = selectedIds.length > 1;

  return (
    <DeckPropertySection title="Ações" hint={E.layerUp} defaultOpen={false}>
      <DeckActionRow>
        {!multiSelect ? (
          <>
            <HintAction hint={E.layerUp} ariaLabel="Ajuda: trazer frente">
              <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("up")}>
                <ArrowUp size={15} aria-hidden="true" />
                Trazer frente
              </button>
            </HintAction>
            <HintAction hint={E.layerDown} ariaLabel="Ajuda: enviar fundo">
              <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("down")}>
                <ArrowDown size={15} aria-hidden="true" />
                Enviar fundo
              </button>
            </HintAction>
          </>
        ) : null}
        <HintAction hint={E.remove} ariaLabel="Ajuda: remover">
          <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={removeSelected}>
            <Trash2 size={15} aria-hidden="true" />
            Remover
          </button>
        </HintAction>
      </DeckActionRow>
    </DeckPropertySection>
  );
}
