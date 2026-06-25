import type { ActionPlanDetail } from "../types/actionPlan";
import { computeRnc8dDisciplineProgress } from "../utils/rnc8dDisciplineProgress";

type Props = {
  detail: ActionPlanDetail;
};

export function Rnc8dDisciplineProgress({ detail }: Props) {
  const { disciplines, percentComplete } = computeRnc8dDisciplineProgress(detail);

  return (
    <div className="pac-rnc8d-progress" aria-label="Progresso das disciplinas 8D">
      <div className="pac-rnc8d-progress__header">
        <strong>Checklist 8D (D0–D8)</strong>
        <span className="pac-muted">{percentComplete}% concluído</span>
      </div>
      <div
        className="pac-rnc8d-progress__bar"
        role="progressbar"
        aria-valuenow={percentComplete}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <span className="pac-rnc8d-progress__bar-fill" style={{ width: `${percentComplete}%` }} />
      </div>
      <ul className="pac-rnc8d-progress__list">
        {disciplines.map((item) => (
          <li
            key={item.id}
            className={
              item.complete ? "pac-rnc8d-progress__item pac-rnc8d-progress__item--done" : "pac-rnc8d-progress__item"
            }
            title={item.hint}
          >
            <span className="pac-rnc8d-progress__id">{item.id}</span>
            <span className="pac-rnc8d-progress__label">{item.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
