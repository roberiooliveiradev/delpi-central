import {
  dataTransformStepFormula,
} from "@delpi/tv-dashboard-presentation";
import { HintAction } from "@delpi/plugin-ui/index";
import type { DataTransformStep } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

const H = TV_DASHBOARD_HELP_TOOLTIPS.dataPrepare;

type Props = {
  step: DataTransformStep | null;
  newColumnDraft?: boolean;
  columnHints?: string[];
  onCommit: (step: DataTransformStep) => void;
  onCancelDraft?: () => void;
  focusToken?: number;
};

/**
 * Barra fx estilo Power Query: edita a etapa selecionada; ✓ aplica, ✕ descarta.
 * Cálculo permanece no backend.
 */
export function DataPrepareFormulaBar({
  step,
  newColumnDraft = false,
}: Props) {
  const value = step ? `= ${dataTransformStepFormula(step)}` : "";

  return (
    <div className="td-data-pq__formula-wrap">
      <HintAction hint={H.formulaBar} ariaLabel="Ajuda: barra de fórmula" placement="bottom">
        <div className="td-data-pq__formula" aria-label="Barra de fórmula">
          <span className="td-data-pq__fx" aria-hidden>
            fx
          </span>
          <code>{value}</code>
        </div>
      </HintAction>
      {step || newColumnDraft ? (
        <p className="td-data-pq__formula-hint">
          Compatibilidade v1: barra somente leitura. Use a faixa de opções; a edição M é habilitada
          pelo servidor.
        </p>
      ) : null}
    </div>
  );
}
