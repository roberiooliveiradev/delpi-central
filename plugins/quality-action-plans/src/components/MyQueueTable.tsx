import { Eye } from "lucide-react";

import {
  ACTION_STATUS_OPTIONS,
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
  savingActionId?: string | null;
  onNavigate: (path: string) => void;
  onStatusChange: (item: MyQueueItem, status: string) => void;
};

export function MyQueueTable({
  items,
  loading,
  emptyMessage,
  savingActionId,
  onNavigate,
  onStatusChange,
}: Props) {
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
              <td>
                <select
                  className="pac-table-select pac-table-select--status"
                  value={
                    ACTION_STATUS_OPTIONS.some((option) => option.value === item.action_status)
                      ? item.action_status
                      : "pending"
                  }
                  aria-label={`Status da ação ${item.plan_code ?? item.action_id}`}
                  title={PAC_HELP_TOOLTIPS.tables.actionStatus}
                  disabled={savingActionId === item.action_id}
                  onChange={(event) => onStatusChange(item, event.target.value)}
                >
                  {ACTION_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </td>
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
