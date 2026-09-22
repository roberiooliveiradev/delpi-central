import type { ReactNode } from "react";

import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { TmStatusBadge } from "../../components/tmChromeUi";
import { cenarioLabel } from "../../content/cenarioLabels";
import type { ProcessoInstancia, Revisao } from "../../data/api/transformometroApi";
import { revisaoDisplayLabel } from "../../utils/revisaoLabels";
import type { ComparisonMode } from "./buildRevisionComparisonView";
import { instanciaNavLabel } from "./processWorkspaceNav";

type Props = {
  instance: ProcessoInstancia;
  toBe: Revisao | null;
  asIs: Revisao | null;
  mode: ComparisonMode;
  canChangeInstance: boolean;
  onChangeInstance: () => void;
  onOpenRevision?: () => void;
  /** Scenario picker rendered inside the same context card (visual integration). */
  scenarioPicker?: ReactNode;
};

export function ResultsContextHeader({
  instance,
  toBe,
  asIs,
  mode,
  canChangeInstance,
  onChangeInstance,
  onOpenRevision,
  scenarioPicker,
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
          Melhoria, cenário proposto e referência usados nesta leitura.
        </p>
      </div>

      <dl className="tm-processo-results-context__grid">
        <div className="tm-processo-results-context__item">
          <dt>Melhoria analisada</dt>
          <dd>{instanciaNavLabel(instance)}</dd>
        </div>
        <div className="tm-processo-results-context__item">
          <dt>Cenário proposto</dt>
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
          <dt>Referência atual (AS-IS)</dt>
          <dd>{referenceLabel}</dd>
        </div>
      </dl>

      {scenarioPicker ? (
        <div className="tm-processo-results-context__scenario">{scenarioPicker}</div>
      ) : null}

      <div className="tm-processo-results-context__actions">
        {canChangeInstance ? (
          <button type="button" className={DS_GHOST_BTN} onClick={onChangeInstance}>
            Trocar melhoria
          </button>
        ) : null}
        {toBe && onOpenRevision ? (
          <button
            type="button"
            className="ds-link tm-processo-results-context__link"
            onClick={onOpenRevision}
          >
            Abrir revisão
          </button>
        ) : null}
      </div>
    </header>
  );
}
