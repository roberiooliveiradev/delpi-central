import { Eye } from "lucide-react";

import { branchLabel, detailPath } from "../constants/actionPlans";
import type { RecurrenceGroup } from "../types/recurrence";
import { formatDateTime } from "../utils/format";

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
            <th>Filial</th>
            <th>Produto</th>
            <th>Modo de falha</th>
            <th>Total</th>
            <th>Abertos</th>
            <th>Críticos abertos</th>
            <th>Último plano</th>
            <th>Última abertura</th>
            <th aria-label="Ações" />
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
