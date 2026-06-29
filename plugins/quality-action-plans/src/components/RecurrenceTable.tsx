import { Eye } from "lucide-react";

import { branchLabel, detailPath } from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RecurrenceGroup } from "../types/recurrence";
import { formatDateTime } from "../utils/format";
import { TableHeaderCell } from "./ui/HelpTooltip";

const T = PAC_HELP_TOOLTIPS.tables;

type Props = {
  items: RecurrenceGroup[];
  loading?: boolean;
  emptyMessage?: string;
  onNavigate: (path: string) => void;
};

export function RecurrenceTable({ items, loading, emptyMessage, onNavigate }: Props) {
  if (loading) {
    return <p className="pac-muted">Carregando recorrências…</p>;
  }

  if (!items.length) {
    return <p className="pac-muted">{emptyMessage ?? "Nenhuma recorrência encontrada."}</p>;
  }

  return (
    <div className="pac-table-wrap">
      <table className="pac-table">
        <thead>
          <tr>
            <TableHeaderCell label="Filial" hint={T.branch} />
            <TableHeaderCell label="Produto" hint={T.product} />
            <TableHeaderCell label="Modo de falha" hint={T.failureMode} />
            <TableHeaderCell label="Total" hint={T.totalPlans} />
            <TableHeaderCell label="Abertos" hint={T.openPlans} />
            <TableHeaderCell label="Críticos abertos" hint={T.criticalOpen} />
            <TableHeaderCell label="Último plano" hint={T.lastPlan} />
            <TableHeaderCell label="Última abertura" hint={T.lastOpened} />
            <TableHeaderCell
              label="Ações"
              hint={T.rowActions}
              className="pac-table__actions-col"
            />
          </tr>
        </thead>
        <tbody>
          {items.map((group) => (
            <tr key={group.recurrence_key}>
              <td>{branchLabel(group.branch_code)}</td>
              <td>{group.product_code ?? "—"}</td>
              <td>{group.failure_mode ?? "—"}</td>
              <td>{group.total_plans}</td>
              <td>{group.open_plans}</td>
              <td>{group.critical_open}</td>
              <td>{group.last_plan_code ?? "—"}</td>
              <td>{formatDateTime(group.last_opened_at)}</td>
              <td>
                {group.last_plan_id ? (
                  <button
                    type="button"
                    className="pac-icon-btn"
                    title="Ver último plano"
                    onClick={() => onNavigate(detailPath(group.last_plan_id!))}
                  >
                    <Eye size={16} aria-hidden />
                  </button>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
