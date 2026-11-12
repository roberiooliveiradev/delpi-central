import { buildPurchaseRequestDetailPath } from "../../app/pluginRoutes";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { SuppliesEmptyState, SuppliesSectionCard } from "../../app/suppliesUi";
import type { ApprovalPendingRequest } from "./approvalLeadTimeApi";
import { ApprovalRequestProducts } from "./ApprovalRequestProducts";

function localDateLabel(value: string | null | undefined): string {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  return year && month && day ? `${day}/${month}/${year}` : value;
}

export function ApprovalLeadTimePendingRequests({
  items,
  total,
  truncated,
  basePath,
}: {
  items: ApprovalPendingRequest[];
  total: number;
  truncated: boolean;
  basePath: string;
}) {
  return (
    <SuppliesSectionCard
      title={`Aguardando aprovação · ${total.toLocaleString("pt-BR")} SCs`}
      hint="Somente etapas ativas com CR_STATUS=02 na SCR. Etapas futuras (01) ainda não estão pendentes para o aprovador."
    >
      {!items.length ? (
        <SuppliesEmptyState title="Nenhuma alçada ativa pendente" message="Não há etapas status 02 na SCR para solicitações ativas deste período." />
      ) : (
        <div className="sp-approval-lead-time__table-scroll">
          <table className="sp-approval-lead-time__table">
            <thead>
              <tr>
                <th>SC</th><th>Filial</th><th>Solicitante</th>
                <th>Produtos (código e descrição)</th><th>Criação da SC</th>
                <th>Aprovador pendente</th><th>Nível</th>
                <th>Aguardando desde</th><th>Dias em aberto</th>
                <th>Consistência</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={`${item.branch}:${item.request_number}`}>
                  <td>
                    <button type="button" className="sp-approval-lead-time__link" onClick={() =>
                      navigatePluginPath(buildPurchaseRequestDetailPath(item.branch, item.request_number, basePath))
                    }>{item.request_number}</button>
                  </td>
                  <td>{item.branch}</td>
                  <td>{item.requester_name || "Não identificado"}</td>
                  <td className="sp-approval-lead-time__product-cell">
                    <ApprovalRequestProducts products={item.products} />
                  </td>
                  <td>{localDateLabel(item.issue_date)}</td>
                  <td className="sp-approval-lead-time__pending-cell">
                    {item.pending_approvers.map((person) => (
                      <div className="sp-approval-lead-time__pending-entry" key={`${person.level}:${person.approver_code}:${person.pending_since}`}>
                        <strong>{person.approver_name || `Aprovador ${person.approver_code}`}</strong>
                        <small>Cód. {person.approver_code}{person.approver_user_code ? ` · Usuário ${person.approver_user_code}` : ""}</small>
                      </div>
                    ))}
                  </td>
                  <td>{item.pending_approvers.map((p) => p.level).join(" · ")}</td>
                  <td>{item.pending_approvers.map((p) => localDateLabel(p.pending_since)).join(" · ")}</td>
                  <td>{item.pending_approvers.map((p) => p.waiting_days == null ? "—" : `${p.waiting_days} d`).join(" · ")}</td>
                  <td>
                    {item.sc1_approved ? (
                      <span className="sp-approval-lead-time__warning">
                        Atenção: SCR pendente, mas itens da SC1010 já estão liberados.
                      </span>
                    ) : "SC aguardando liberação"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {truncated ? <p className="sp-approval-lead-time__table-note">São exibidas as 100 SCs pendentes mais recentes no período; o total é completo.</p> : null}
    </SuppliesSectionCard>
  );
}
