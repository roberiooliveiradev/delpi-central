import type { NcDueSlaLevel } from "../types/ncManagement";
import { dueSlaHint, dueSlaLabel } from "../utils/ncDueSla";

type Props = {
  level: NcDueSlaLevel;
  daysUntilDue: number | null;
};

export function NcDueSlaPill({ level, daysUntilDue }: Props) {
  return (
    <span
      className={`a5s-nc-board-sla a5s-nc-board-sla--${level}`}
      title={dueSlaHint(level, daysUntilDue)}
    >
      {dueSlaLabel(level)}
    </span>
  );
}
