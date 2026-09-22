import { HelpTooltip } from "@delpi/plugin-ui/index";

import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { TmStatusBadge } from "../../components/tmChromeUi";
import { cenarioLabel } from "../../content/cenarioLabels";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { ProcessoInstancia, Revisao } from "../../data/api/transformometroApi";
import { revisaoDisplayLabel } from "../../utils/revisaoLabels";
import type { ComparisonMode } from "./buildRevisionComparisonView";
import { instanciaNavLabel } from "./processWorkspaceNav";

const H = TM_HELP_TOOLTIPS.resultados;

type Props = {
  instance: ProcessoInstancia;
  toBe: Revisao | null;
  asIs: Revisao | null;
  mode: ComparisonMode;
  canChangeInstance: boolean;
  onChangeInstance: () => void;
  onOpenRevision?: () => void;
};

export function ResultsContextHeader({
  instance,
  toBe,
  asIs,
  mode,
  canChangeInstance,
  onChangeInstance,
  onOpenRevision,
}: Props) {
  const referenceLabel =
    mode === "legacy_reference_missing" || mode === "reference_not_in_scope"
      ? "Não definida"
      : asIs
        ? `${revisaoDisplayLabel(asIs)} · ${cenarioLabel(asIs.cenario_tipo)}`
        : mode === "baseline_only"
          ? "Linha de base (própria)"
          : "—";

  return (
    <header className="tm-processo-results-context" aria-label="Contexto da comparação">
      <div className="tm-processo-results-context__intro">
        <h3 className="tm-processo-results-context__heading">Contexto da comparação</h3>
        <p className="tm-processo-results-context__lede">
          Confira a melhoria, o cenário proposto e a referência usada na comparação.
        </p>
      </div>

      <dl className="tm-processo-results-context__grid">
        <div className="tm-processo-results-context__item">
          <dt>
            Melhoria analisada
            <HelpTooltip
              content="Melhoria operacional (instância) cujo cenário você está analisando."
              ariaLabel="Ajuda: Melhoria analisada"
            />
          </dt>
          <dd>{instanciaNavLabel(instance)}</dd>
        </div>
        <div className="tm-processo-results-context__item">
          <dt>
            Cenário proposto
            <HelpTooltip content={H.toBe} ariaLabel="Ajuda: Cenário proposto" />
          </dt>
          <dd>
            {toBe ? (
              <>
                <span>
                  {revisaoDisplayLabel(toBe)} · {cenarioLabel(toBe.cenario_tipo)}
                </span>
                {!toBe.revisao_ativa ? (
                  <TmStatusBadge label="inativa" variant="neutral" />
                ) : (
                  <TmStatusBadge label="ativa" variant="success" />
                )}
              </>
            ) : (
              "—"
            )}
          </dd>
        </div>
        <div className="tm-processo-results-context__item">
          <dt>
            Referência atual
            <HelpTooltip content={H.asIs} ariaLabel="Ajuda: Referência atual" />
          </dt>
          <dd>{referenceLabel}</dd>
        </div>
      </dl>

      <div className="tm-processo-results-context__actions">
        {canChangeInstance ? (
          <button type="button" className={DS_GHOST_BTN} onClick={onChangeInstance}>
            Trocar melhoria
          </button>
        ) : null}
        {toBe && onOpenRevision ? (
          <button type="button" className="ds-link tm-processo-results-context__link" onClick={onOpenRevision}>
            Abrir revisão
          </button>
        ) : null}
      </div>
    </header>
  );
}
