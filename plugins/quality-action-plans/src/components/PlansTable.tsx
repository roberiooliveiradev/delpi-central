import { TableHeaderCell } from "./ui/TableHeaderCell";
import { Eye } from "lucide-react";

import { branchLabel, detailPath } from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ActionPlanSummary } from "../types/actionPlan";
import { formatDateTime } from "../utils/format";
import { PlanSlaBadge } from "./PlanSlaBadge";
import { ScopeBadge, SeverityBadge, StatusBadge } from "./StatusBadge";

const T = PAC_HELP_TOOLTIPS.tables;

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
            <TableHeaderCell label="Código" hint={T.code} />
            <TableHeaderCell label="Título" hint={T.title} />
            <TableHeaderCell label="Cliente" hint={T.customer} />
            <TableHeaderCell label="Filial" hint={T.branch} />
            <TableHeaderCell label="Escopo" hint={T.scope} />
            <TableHeaderCell label="Produto" hint={T.product} />
            <TableHeaderCell label="Severidade" hint={T.severity} />
            <TableHeaderCell label="Status" hint={T.status} />
            <TableHeaderCell label="SLA" hint={T.sla} />
            <TableHeaderCell label="Atualizado" hint={T.updatedAt} />
            <TableHeaderCell
              label="Ações"
              hint={T.rowActions}
              className="pac-table__actions-col"
            />
          </tr>
        </thead>
        <tbody>
          {items.map((plan) => (
            <tr
              key={plan.id}
              className={plan.sla_level === "breached" ? "pac-table__row--sla-breached" : undefined}
            >
              <td>{plan.code ?? "—"}</td>
              <td>{plan.title}</td>
              <td>{plan.customer_name ?? "—"}</td>
              <td>{branchLabel(plan.branch_code)}</td>
              <td>
                <ScopeBadge scope={plan.nonconformity_scope} />
              </td>
              <td>{plan.product_code ?? "—"}</td>
              <td>
                <SeverityBadge severity={plan.severity} />
              </td>
              <td>
                <StatusBadge status={plan.status} />
              </td>
              <td>
                <PlanSlaBadge plan={plan} />
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
