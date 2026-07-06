import { FieldLabel } from "../HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { InstanciaContextoV1 } from "../../types/decomposition";

const C = TM_HELP_TOOLTIPS.decomposition;

type Props = {
  contexto: InstanciaContextoV1;
};

function displayValue(value?: string | null): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : "—";
}

export function InstanciaContextoReadView({ contexto }: Props) {
  return (
    <dl className="ds-dl-grid">
      <div>
        <dt>
          <FieldLabel label="Responsável local" hint={C.contextoResponsavel} />
        </dt>
        <dd>{displayValue(contexto.responsavel_local)}</dd>
      </div>
      <div>
        <dt>
          <FieldLabel label="Contato" hint={C.contextoContato} />
        </dt>
        <dd>{displayValue(contexto.contato)}</dd>
      </div>
      <div className="ds-dl-grid__full">
        <dt>
          <FieldLabel label="Observações de rollout" hint={C.contextoObservacoesRollout} />
        </dt>
        <dd>{displayValue(contexto.observacoes_rollout)}</dd>
      </div>
    </dl>
  );
}
