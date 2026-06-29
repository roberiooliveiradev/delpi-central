import { Eye } from "lucide-react";

import {
  ACTION_STATUSES,
  actionTypeLabel,
  branchLabel,
  detailPath,
} from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { MyQueueItem } from "../types/myQueue";
import { formatDate } from "../utils/format";
import { TableHeaderCell } from "./ui/HelpTooltip";

const T = PAC_HELP_TOOLTIPS.tables;

type Props = {
  items: MyQueueItem[];
  loading?: boolean;
  emptyMessage?: string;
  onNavigate: (path: string) => void;
};

export function MyQueueTable({ items, loading, emptyMessage, onNavigate }: Props) {
  if (loading) {
    return <p className="pac-muted">Carregando sua fila…</p>;
  }

  if (!items.length) {
    return <p className="pac-muted">{emptyMessage ?? "Nenhuma ação pendente para você."}</p>;
  }

  return (
    <div className="pac-table-wrap">
      <table className="pac-table">
        <thead>
          <tr>
            <TableHeaderCell label="Plano" hint={T.plan} />
            <TableHeaderCell label="Ação" hint={T.action} />
            <TableHeaderCell label="Tipo" hint={T.actionType} />
            <TableHeaderCell label="Prazo" hint={T.dueDate} />
            <TableHeaderCell label="Status" hint={T.actionStatus} />
            <TableHeaderCell label="Filial" hint={T.branch} />
            <TableHeaderCell label="Cliente" hint={T.customer} />
            <TableHeaderCell
              label="Ações"
              hint={T.rowActions}
              className="pac-table__actions-col"
            />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.action_id}
              className={item.is_overdue ? "pac-table__row--overdue" : undefined}
            >
              <td>
                <strong>{item.plan_code ?? "—"}</strong>
                <p className="pac-muted pac-table__subline">{item.plan_title}</p>
              </td>
              <td>{item.description}</td>
              <td>{actionTypeLabel(item.action_type)}</td>
              <td>
                {item.is_overdue ? (
                  <span className="pac-badge pac-badge--warning pac-table__overdue-badge">Atrasada</span>
                ) : item.is_due_soon ? (
                  <span className="pac-badge pac-badge--sla pac-badge--sla-due-soon pac-table__overdue-badge">
                    Vence em {item.days_until_due ?? 0}d
                  </span>
                ) : null}
                <span>{formatDate(item.due_date)}</span>
              </td>
              <td>{ACTION_STATUSES[item.action_status] ?? item.action_status}</td>
              <td>{branchLabel(item.branch_code)}</td>
              <td>{item.customer_name ?? "—"}</td>
              <td>
                <button
                  type="button"
                  className="pac-icon-btn"
                  title="Abrir plano"
                  onClick={() => onNavigate(detailPath(item.plan_id))}
                >
                  <Eye size={16} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
