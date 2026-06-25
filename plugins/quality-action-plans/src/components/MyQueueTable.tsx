import { Eye } from "lucide-react";

import {
  ACTION_STATUSES,
  actionTypeLabel,
  branchLabel,
  detailPath,
} from "../constants/actionPlans";
import type { MyQueueItem } from "../types/myQueue";
import { formatDate } from "../utils/format";

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
            <th>Plano</th>
            <th>Ação</th>
            <th>Tipo</th>
            <th>Prazo</th>
            <th>Status</th>
            <th>Filial</th>
            <th>Cliente</th>
            <th aria-label="Ações" />
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
