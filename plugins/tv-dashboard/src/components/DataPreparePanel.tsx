import { HintAction } from "@delpi/plugin-ui/index";
import type { ComunicadoDataSourceBlock } from "@delpi/tv-dashboard-presentation";
import { Database } from "lucide-react";
import { useState } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DataPrepareModal } from "./DataPrepareModal";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  block: ComunicadoDataSourceBlock;
};

/**
 * Entrada no inspetor: abre o ambiente Power Query em modal (rotas = consultas).
 */
export function DataPreparePanel({ pane = false, block }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <DeckPropertySection
        pane={pane}
        title="Preparar dados"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.prepareData}
        defaultOpen
      >
        <p className="td-deck-inspector__hint">
          Ambiente tipo Power Query: prévia tabular, etapas aplicadas e transformações na rota
          api-delpi (não no visual).
        </p>
        <HintAction
          hint={TV_DASHBOARD_HELP_TOOLTIPS.dataPrepare.modal}
          ariaLabel="Ajuda: abrir preparação de dados"
          placement="bottom"
        >
          <button type="button" className="td-btn td-btn--sm" onClick={() => setOpen(true)}>
            <Database size={14} aria-hidden />
            Abrir preparação de dados…
          </button>
        </HintAction>
      </DeckPropertySection>
      <DataPrepareModal
        open={open}
        onClose={() => setOpen(false)}
        initialSourceId={block.id}
      />
    </>
  );
}
