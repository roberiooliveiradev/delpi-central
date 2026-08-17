import type { NcBoardItem } from "../types/ncManagement";
import { computeNcBoardProgressPct } from "../utils/ncBoardProgress";

type Props = {
  item: Pick<
    NcBoardItem,
    | "status"
    | "description"
    | "root_cause"
    | "corrective_action"
    | "responsible_name"
    | "due_date"
    | "has_before_evidence"
    | "has_after_evidence"
  >;
};

export function NcBoardProgressBar({ item }: Props) {
  const pct = computeNcBoardProgressPct(item);

  return (
    <div className="a5s-nc-board-progress">
      <div className="a5s-progress__track">
        <div
          className="a5s-progress__fill"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Progresso do plano de ação: ${pct}%`}
        />
      </div>
      <span className="a5s-nc-board-progress__pct">{pct}%</span>
    </div>
  );
}
