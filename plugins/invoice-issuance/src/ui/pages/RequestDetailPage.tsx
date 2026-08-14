import { useEffect, useState } from "react";
import { useIssuancePermissions } from "../../application/useIssuancePermissions";
import { II_SHEET } from "../../content/helpTooltips";
import { hasAction, historyEventLabel, invoiceTypeLabel } from "../../domain/status";
import * as api from "../../data/api/invoiceIssuanceApi";
import { ApiError } from "../../data/api/httpClient";
import type { AllowedAction, IssuanceRequest, RequestDetail } from "../../domain/types";
import { CopyableValue } from "../components/CopyableValue";
import { IssuanceProtheusSheet } from "../components/IssuanceProtheusSheet";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime, formatMoney, formatQuantity, itemTotal } from "../format";

type Props = {
  requestId: string;
  onBack: () => void;
  onEdit: () => void;
};

export function RequestDetailPage({ requestId, onBack, onEdit }: Props) {
  const perms = useIssuancePermissions();
  const [detail, setDetail] = useState<RequestDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [returnReason, setReturnReason] = useState("");
  const [cancelJustification, setCancelJustification] = useState("");

  async function reload() {
    const data = await api.getRequest(requestId);
    setDetail(data);
  }

  useEffect(() => {
    setError(null);
    reload().catch((err: unknown) => {
      setError(err instanceof ApiError ? err.message : "Falha ao carregar o detalhe.");
    });
  }, [requestId]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      await reload();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Operação não concluída.");
    } finally {
      setBusy(false);
    }
  }

  if (!detail) {
    return (
      <div className="ii-stack" data-testid="detail-page">
        {error ? <div className="ii-alert ii-error">{error}</div> : <p>Carregando…</p>}
      </div>
    );
  }

  const { request, history, allowed_actions } = detail;
  const total = request.items.reduce(
    (sum, item) => sum + itemTotal(item.quantity, item.unit_price),
    0,
  );
  const needsReturn = hasAction(allowed_actions, "return");
  const needsCancel = hasAction(allowed_actions, "cancel");

  return (
    <div className="ii-stack" data-testid="detail-page">
      <PageHeader
        title={request.party_name}
        subtitle={`${request.party_code}/${request.party_store} · ${invoiceTypeLabel(request.invoice_type)}`}
        actions={
          <DetailHeaderActions
            allowedActions={allowed_actions}
            busy={busy}
            onBack={onBack}
            onEdit={onEdit}
            onStart={() => void run(() => api.startRequest(request.id))}
            onIssue={() => void run(() => api.issueRequest(request.id))}
          />
        }
        meta={<StatusBadge status={request.status} />}
      />

      {error ? (
        <div className="ii-alert ii-error" role="alert">
          {error}
        </div>
      ) : null}

      {request.return_reason ? (
        <div className="ii-alert">Motivo da devolução: {request.return_reason}</div>
      ) : null}

      <IssuanceProtheusSheet request={request} />

      <section className="ii-card">
        <h2>{II_SHEET.items}</h2>
        <div className="ii-table-wrap">
          <ItemsTable request={request} total={total} />
        </div>
      </section>

      {needsReturn || needsCancel ? (
        <section className="ii-card">
          <h2>{II_SHEET.actions}</h2>
          <div className="ii-actions">
            {needsReturn ? (
              <div className="ii-inline-form">
                <input
                  aria-label="Motivo da devolução"
                  placeholder="Motivo da devolução"
                  value={returnReason}
                  onChange={(event) => setReturnReason(event.target.value)}
                />
                <button
                  type="button"
                  className="ii-btn"
                  disabled={busy || !returnReason.trim()}
                  onClick={() =>
                    void run(() => api.returnRequest(request.id, returnReason.trim()))
                  }
                >
                  Devolver
                </button>
              </div>
            ) : null}
            {needsCancel ? (
              <div className="ii-inline-form">
                <input
                  aria-label="Justificativa do cancelamento"
                  placeholder="Justificativa"
                  value={cancelJustification}
                  onChange={(event) => setCancelJustification(event.target.value)}
                />
                <button
                  type="button"
                  className="ii-btn ii-btn--danger"
                  disabled={busy || !cancelJustification.trim()}
                  onClick={() =>
                    void run(() => api.cancelRequest(request.id, cancelJustification.trim()))
                  }
                >
                  Cancelar
                </button>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      {!perms.canProcess && allowed_actions.length <= 1 ? (
        <p className="ii-muted">Acompanhe o andamento nesta tela.</p>
      ) : null}

      <section className="ii-card">
        <h2>{II_SHEET.history}</h2>
        <ol className="ii-history">
          {history.map((event) => (
            <li key={event.id}>
              <strong>{historyEventLabel(event.event_type)}</strong> · {event.actor_name || "sistema"} ·{" "}
              {formatDateTime(event.created_at)}
              {event.justification ? ` — ${event.justification}` : ""}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function DetailHeaderActions({
  allowedActions,
  busy,
  onBack,
  onEdit,
  onStart,
  onIssue,
}: {
  allowedActions: AllowedAction[];
  busy: boolean;
  onBack: () => void;
  onEdit: () => void;
  onStart: () => void;
  onIssue: () => void;
}) {
  return (
    <>
      <button type="button" className="ii-btn ii-btn--ghost" onClick={onBack}>
        Voltar
      </button>
      {hasAction(allowedActions, "edit") ? (
        <button type="button" className="ii-btn ii-btn--primary" onClick={onEdit}>
          Corrigir e reenviar
        </button>
      ) : null}
      {hasAction(allowedActions, "start") ? (
        <button type="button" className="ii-btn ii-btn--primary" disabled={busy} onClick={onStart}>
          Iniciar atendimento
        </button>
      ) : null}
      {hasAction(allowedActions, "issue") ? (
        <button type="button" className="ii-btn ii-btn--primary" disabled={busy} onClick={onIssue}>
          Marcar emitida
        </button>
      ) : null}
    </>
  );
}

function ItemsTable({ request, total }: { request: IssuanceRequest; total: number }) {
  return (
    <table className="ii-table">
      <thead>
        <tr>
          <th>Produto</th>
          <th>Descrição</th>
          <th>Pedido</th>
          <th>Item</th>
          <th className="ii-cell-num">Qtd</th>
          <th className="ii-cell-num">Valor unit.</th>
          <th>Baixa</th>
          <th className="ii-cell-num">Total</th>
        </tr>
      </thead>
      <tbody>
        {request.items.map((item, index) => (
          <tr key={`${item.product_code}-${item.line_number ?? index}`}>
            <td>
              <CopyableValue value={item.product_code} label="Produto">
                {item.product_code}
              </CopyableValue>
            </td>
            <td>{item.product_description}</td>
            <td>
              {item.sales_order ? (
                <CopyableValue value={item.sales_order} label="Pedido">
                  {item.sales_order}
                </CopyableValue>
              ) : (
                "—"
              )}
            </td>
            <td>{item.sales_order_item || "—"}</td>
            <td className="ii-cell-num">{formatQuantity(item.quantity)}</td>
            <td className="ii-cell-num">{formatMoney(item.unit_price)}</td>
            <td>{item.stock_write_off ? "Sim" : "Não"}</td>
            <td className="ii-cell-num ii-cell-strong">
              {formatMoney(itemTotal(item.quantity, item.unit_price))}
            </td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr>
          <td colSpan={7} className="ii-cell-strong">
            Total
          </td>
          <td className="ii-cell-num ii-cell-strong">{formatMoney(total)}</td>
        </tr>
      </tfoot>
    </table>
  );
}
