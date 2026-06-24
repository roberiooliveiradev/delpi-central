import { Eye } from "lucide-react";

import { branchLabel, detailPath } from "../constants/actionPlans";
import type { ActionPlanSummary } from "../types/actionPlan";
import { formatDateTime } from "../utils/format";
import { SeverityBadge, StatusBadge } from "./StatusBadge";

type Props = {
  items: ActionPlanSummary[];
  loading?: boolean;
  emptyMessage?: string;
  onNavigate: (path: string) => void;
};

export function PlansTable({ items, loading, emptyMessage, onNavigate }: Props) {
  if (loading) {
    return <p className="pac-muted">Carregando planos…</p>;
  }

  if (!items.length) {
    return <p className="pac-muted">{emptyMessage ?? "Nenhum plano encontrado."}</p>;
  }

  return (
    <div className="pac-table-wrap">
      <table className="pac-table">
        <thead>
          <tr>
            <th>Código</th>
            <th>Título</th>
            <th>Cliente</th>
            <th>Filial</th>
            <th>Produto</th>
            <th>Severidade</th>
            <th>Status</th>
            <th>Atualizado</th>
            <th aria-label="Ações" />
          </tr>
        </thead>
        <tbody>
          {items.map((plan) => (
            <tr key={plan.id}>
              <td>{plan.code ?? "—"}</td>
              <td>{plan.title}</td>
              <td>{plan.customer_name ?? "—"}</td>
              <td>{branchLabel(plan.branch_code)}</td>
              <td>{plan.product_code ?? "—"}</td>
              <td>
                <SeverityBadge severity={plan.severity} />
              </td>
              <td>
                <StatusBadge status={plan.status} />
              </td>
              <td>{formatDateTime(plan.updated_at)}</td>
              <td>
                <button
                  type="button"
                  className="pac-icon-btn"
                  title="Ver detalhe"
                  onClick={() => onNavigate(detailPath(plan.id))}
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
