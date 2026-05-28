import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import { formatStrategicIndicatorsErrorLocation } from "../../data/errors/strategicIndicatorsError";
import "./StrategicIndicatorsErrorState.css";

type StrategicIndicatorsErrorStateProps = {
  error: StrategicIndicatorsErrorView;
  actionLabel?: string;
  onAction?: () => void;
  /** Corpo do modal: sem card, título e resumo duplicados. */
  embedded?: boolean;
};

export function StrategicIndicatorsErrorState({
  error,
  actionLabel,
  onAction,
  embedded = false,
}: StrategicIndicatorsErrorStateProps) {
  const shouldRenderAction = Boolean(actionLabel && onAction && !embedded);
  const location = formatStrategicIndicatorsErrorLocation(error);

  return (
    <div
      className={
        embedded ? "si-error-state si-error-state--embedded" : "si-error-state"
      }
    >
      {embedded ? null : (
        <div className="si-error-state__icon" aria-hidden>
          !
        </div>
      )}

      <div className="si-error-state__content">
        {embedded ? null : (
          <>
            <h3 className="si-error-state__title">{error.title}</h3>
            <p className="si-error-state__summary">{error.summary}</p>
          </>
        )}

        <dl className="si-error-state__meta">
          <div className="si-error-state__meta-row">
            <dt>Onde</dt>
            <dd>{error.context.surface}</dd>
          </div>
          <div className="si-error-state__meta-row">
            <dt>Recorte</dt>
            <dd>{location}</dd>
          </div>
        </dl>

        {error.causes.length ? (
          <section className="si-error-state__section">
            <h4 className="si-error-state__section-title">Possíveis causas</h4>
            <ul className="si-error-state__list">
              {error.causes.map((cause) => (
                <li key={cause}>{cause}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {error.suggestions.length ? (
          <section className="si-error-state__section">
            <h4 className="si-error-state__section-title">O que fazer</h4>
            <ul className="si-error-state__list">
              {error.suggestions.map((suggestion) => (
                <li key={suggestion}>{suggestion}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {error.technicalDetail ? (
          <details className="si-error-state__technical">
            <summary>Detalhe técnico</summary>
            <pre>{error.technicalDetail}</pre>
          </details>
        ) : null}

        {shouldRenderAction ? (
          <button
            type="button"
            className="si-error-state__action"
            onClick={onAction}
          >
            {actionLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}
