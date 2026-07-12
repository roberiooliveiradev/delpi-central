import { useMemo } from "react";

import type { AuditDetail } from "../api/audit5sApi";
import {
  computeSensoSummaries,
  formatPercentual,
  scoreTone,
} from "../utils/sensoScores";

type Props = {
  audit: AuditDetail;
  sensoNamesByOrder: Map<number, string>;
  activeSenso: number;
  onSelectSenso: (order: number) => void;
};

export function AuditSensoScoreCards({
  audit,
  sensoNamesByOrder,
  activeSenso,
  onSelectSenso,
}: Props) {
  const summaries = useMemo(
    () => computeSensoSummaries(audit, sensoNamesByOrder),
    [audit, sensoNamesByOrder],
  );

  return (
    <section
      id="a5s-senso-nav"
      className="a5s-senso-scores"
      aria-label="Média por senso"
    >
      <div className="a5s-senso-scores__header">
        <h3 className="a5s-senso-scores__title">Média por senso</h3>
        <p className="a5s-senso-scores__subtitle">
          Percentual atualizado em tempo real conforme os auditores preenchem.
        </p>
      </div>

      <div className="a5s-senso-scores__grid">
        {summaries.map((item) => {
          const tone = scoreTone(item.percentual);
          const completionPct =
            item.total > 0 ? Math.round((item.scored / item.total) * 100) : 0;
          const isActive = activeSenso === item.order;

          return (
            <button
              key={item.order}
              type="button"
              className={`a5s-senso-score-card a5s-senso-score-card--${tone} ${
                isActive ? "a5s-senso-score-card--active" : ""
              }`}
              aria-pressed={isActive}
              aria-label={`Senso ${item.order}: ${item.name}, ${formatPercentual(item.percentual)}`}
              onClick={() => onSelectSenso(item.order)}
            >
              <span className="a5s-senso-score-card__order">Senso {item.order}</span>
              <span className="a5s-senso-score-card__name">{item.name}</span>
              <strong className="a5s-senso-score-card__value">
                {formatPercentual(item.percentual)}
              </strong>
              <span className="a5s-senso-score-card__hint">
                {item.scored}/{item.total} critérios
              </span>
              <span className="a5s-senso-score-card__track" aria-hidden>
                <span
                  className="a5s-senso-score-card__fill"
                  style={{ width: `${completionPct}%` }}
                />
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
