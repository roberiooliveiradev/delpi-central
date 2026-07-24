import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoicePostingApi";
import type { InvoicePostingDetail } from "../../domain/types";
import { blockReasonLabel, hasAction, statusLabel } from "../../domain/status";
import { BlockModal } from "../components/BlockModal";
import { CancelModal } from "../components/CancelModal";
import { LnfPageHeader } from "../components/LnfPageHeader";
import { ManualPostModal } from "../components/ManualPostModal";
import { StatusBadge } from "../components/StatusBadge";
import {
  formatDate,
  formatDateTime,
  formatDocument,
  formatMoney,
  historyEventLabel,
  postingLeadTimeLabel,
} from "../format";

type Props = {
  requestId: string;
  onBack: () => void;
  onEdit: () => void;
};

export function RequestDetailPage({ requestId, onBack, onEdit }: Props) {
  const [detail, setDetail] = useState<InvoicePostingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [manualPostOpen, setManualPostOpen] = useState(false);
  const [comment, setComment] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRequest(requestId);
      setDetail(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError(err.message);
      } else if (err instanceof ApiError && err.status === 404) {
        setError("Solicitação não encontrada.");
      } else {
        setError(err instanceof Error ? err.message : "Falha ao carregar detalhes.");
      }
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [requestId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(fn: () => Promise<unknown>) {
    setBusy(true);
    setActionError(null);
    try {
      await fn();
      await load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha na ação.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <p data-testid="detail-loading">Carregando detalhes…</p>;
  }

  if (error || !detail) {
    return (
      <div className="lnf-stack">
        <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onBack}>
          Voltar à fila
        </button>
        <p className="lnf-error" role="alert" data-testid="detail-error">
          {error || "Solicitação indisponível."}
        </p>
      </div>
    );
  }

  const { request, history, comments, allowed_actions } = detail;
  const completionLabel =
    request.completion_source === "auto"
      ? "Automática (Protheus)"
      : request.completion_source === "manual"
        ? "Confirmada no plugin"
        : null;
  const leadTime = postingLeadTimeLabel(request, history);

  return (
    <div className="lnf-stack lnf-stack--detail" data-testid="detail-page">
      <LnfPageHeader
        title="Detalhes da solicitação"
        subtitle={`${formatDocument(request.document_number, request.series)} · Filial ${request.branch_code}`}
        actions={
          <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onBack}>
            Voltar
          </button>
        }
      />

      <div className="lnf-detail-board">
        <div className="lnf-detail-board__primary">
          <section className="lnf-card lnf-detail-summary">
            <div className="lnf-detail-summary__status">
              <h2>Resumo</h2>
              <StatusBadge status={request.status} />
            </div>
            <div className="lnf-detail-summary__facts">
              <div>
                <span className="lnf-muted">Valor</span>
                <strong>{formatMoney(Number(request.amount))}</strong>
              </div>
              <div>
                <span className="lnf-muted">Recebimento</span>
                <strong>{formatDateTime(request.received_at)}</strong>
              </div>
              <div>
                <span className="lnf-muted">Fornecedor</span>
                <strong>{request.supplier_name}</strong>
              </div>
              {leadTime ? (
                <div data-testid="posting-lead-time">
                  <span className="lnf-muted">Tempo até lançamento</span>
                  <strong>{leadTime}</strong>
                </div>
              ) : null}
            </div>
            <div className="lnf-actions lnf-actions--compact" data-testid="detail-actions">
              {hasAction(allowed_actions, "start") ? (
                <button
                  type="button"
                  className="lnf-btn lnf-btn--primary"
                  disabled={busy}
                  onClick={() => runAction(() => api.startRequest(requestId))}
                >
                  Iniciar atendimento
                </button>
              ) : null}
              {hasAction(allowed_actions, "block") ? (
                <button
                  type="button"
                  className="lnf-btn lnf-btn--ghost"
                  disabled={busy}
                  onClick={() => setBlockOpen(true)}
                >
                  Bloquear
                </button>
              ) : null}
              {hasAction(allowed_actions, "resume") ? (
                <button
                  type="button"
                  className="lnf-btn lnf-btn--primary"
                  disabled={busy}
                  onClick={() => runAction(() => api.resumeRequest(requestId))}
                >
                  Retomar
                </button>
              ) : null}
              {hasAction(allowed_actions, "edit") ? (
                <button
                  type="button"
                  className="lnf-btn lnf-btn--ghost"
                  disabled={busy}
                  onClick={onEdit}
                >
                  Corrigir
                </button>
              ) : null}
              {hasAction(allowed_actions, "post_manual") ? (
                <button
                  type="button"
                  className="lnf-btn lnf-btn--primary"
                  disabled={busy}
                  onClick={() => setManualPostOpen(true)}
                  data-testid="btn-post-manual"
                >
                  Já lançada
                </button>
              ) : null}
              {hasAction(allowed_actions, "cancel") ? (
                <button
                  type="button"
                  className="lnf-btn lnf-btn--danger"
                  disabled={busy}
                  onClick={() => setCancelOpen(true)}
                >
                  Cancelar
                </button>
              ) : null}
            </div>
            {actionError ? (
              <p className="lnf-error" role="alert">
                {actionError}
              </p>
            ) : null}
          </section>

          <div className="lnf-detail-board__split">
            <section className="lnf-card lnf-detail-panel">
              <h2>Dados fiscais</h2>
              <dl className="lnf-dl lnf-dl--dense">
                <div>
                  <dt>Filial</dt>
                  <dd>{request.branch_code}</dd>
                </div>
                <div>
                  <dt>Nota</dt>
                  <dd>{formatDocument(request.document_number, request.series)}</dd>
                </div>
                <div>
                  <dt>Emissão</dt>
                  <dd>{formatDate(request.issue_date)}</dd>
                </div>
                <div>
                  <dt>Valor</dt>
                  <dd>{formatMoney(Number(request.amount))}</dd>
                </div>
                <div className="lnf-dl__span">
                  <dt>Fornecedor</dt>
                  <dd>
                    <div className="lnf-cell-strong">{request.supplier_name}</div>
                    {request.supplier_short_name ? (
                      <div className="lnf-cell-sub">
                        Nome reduzido: {request.supplier_short_name}
                      </div>
                    ) : null}
                    <div className="lnf-muted lnf-cell-sub">
                      {request.supplier_code}/{request.supplier_store}
                    </div>
                  </dd>
                </div>
                {request.observation ? (
                  <div className="lnf-dl__span">
                    <dt>Observação</dt>
                    <dd>{request.observation}</dd>
                  </div>
                ) : null}
              </dl>
            </section>

            <section className="lnf-card lnf-detail-panel">
              <h2>Situação atual</h2>
              <dl className="lnf-dl lnf-dl--dense">
                <div>
                  <dt>Status</dt>
                  <dd>
                    <StatusBadge status={request.status} />
                  </dd>
                </div>
                <div>
                  <dt>Solicitante</dt>
                  <dd>{request.created_by_name}</dd>
                </div>
                <div>
                  <dt>Responsável</dt>
                  <dd>{request.assignee_name || "—"}</dd>
                </div>
                {completionLabel ? (
                  <div>
                    <dt>Conclusão</dt>
                    <dd>{completionLabel}</dd>
                  </div>
                ) : null}
                {leadTime ? (
                  <div>
                    <dt>Tempo até lançamento</dt>
                    <dd>{leadTime}</dd>
                  </div>
                ) : null}
                {request.erp_entry_date ? (
                  <div>
                    <dt>Digitação no ERP</dt>
                    <dd>{formatDate(request.erp_entry_date)}</dd>
                  </div>
                ) : null}
                {request.reconciled_at ? (
                  <div>
                    <dt>Conciliado em</dt>
                    <dd>{formatDateTime(request.reconciled_at)}</dd>
                  </div>
                ) : null}
                {request.status === "blocked" ? (
                  <>
                    <div className="lnf-dl__span">
                      <dt>Motivo da pendência</dt>
                      <dd>{blockReasonLabel(request.block_reason)}</dd>
                    </div>
                    <div className="lnf-dl__span">
                      <dt>Descrição</dt>
                      <dd>{request.block_description}</dd>
                    </div>
                  </>
                ) : null}
                {request.status === "cancelled" ? (
                  <>
                    <div>
                      <dt>Cancelado por</dt>
                      <dd>{request.cancelled_by_name}</dd>
                    </div>
                    <div>
                      <dt>Em</dt>
                      <dd>{formatDateTime(request.cancelled_at)}</dd>
                    </div>
                    <div className="lnf-dl__span">
                      <dt>Justificativa</dt>
                      <dd>{request.cancel_justification}</dd>
                    </div>
                  </>
                ) : null}
              </dl>
              {request.divergence_alert ? (
                <p className="lnf-warn" role="status">
                  {request.divergence_detail || "Há alerta de divergência com o Protheus."}
                </p>
              ) : null}
            </section>
          </div>
        </div>

        <section className="lnf-card lnf-detail-history">
          <h2>Histórico e comentários</h2>
          {history.length === 0 && comments.length === 0 ? (
            <p className="lnf-muted">Sem eventos ou comentários.</p>
          ) : (
            <ol className="lnf-timeline">
              {history.map((event) => (
                <li
                  key={event.id}
                  className={
                    event.actor_origin === "system"
                      ? "lnf-timeline__item lnf-timeline__item--system"
                      : "lnf-timeline__item lnf-timeline__item--user"
                  }
                >
                  <div className="lnf-timeline__meta">
                    <strong>{historyEventLabel(event.event_type)}</strong>
                    <span className="lnf-muted">{formatDateTime(event.created_at)}</span>
                  </div>
                  <div className="lnf-muted">
                    {event.actor_origin === "system"
                      ? "Sistema"
                      : event.actor_name || "Usuário"}
                    {event.from_status || event.to_status
                      ? ` · ${statusLabel(event.from_status || "")} → ${statusLabel(event.to_status || "")}`
                      : ""}
                  </div>
                  {event.justification ? <p>{event.justification}</p> : null}
                </li>
              ))}
              {comments.map((c) => (
                <li key={c.id} className="lnf-timeline__item lnf-timeline__item--comment">
                  <div className="lnf-timeline__meta">
                    <strong>Comentário</strong>
                    <span className="lnf-muted">{formatDateTime(c.created_at)}</span>
                  </div>
                  <div className="lnf-muted">{c.author_name}</div>
                  <p>{c.body}</p>
                </li>
              ))}
            </ol>
          )}

          {hasAction(allowed_actions, "comment") ? (
            <form
              className="lnf-comment-form"
              onSubmit={(e) => {
                e.preventDefault();
                const text = comment.trim();
                if (!text || busy) return;
                void runAction(async () => {
                  await api.addComment(requestId, text);
                  setComment("");
                });
              }}
            >
              <label className="lnf-field">
                Novo comentário
                <textarea
                  aria-label="Novo comentário"
                  rows={2}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  data-testid="comment-input"
                />
              </label>
              <button
                type="submit"
                className="lnf-btn lnf-btn--primary"
                disabled={busy || !comment.trim()}
              >
                Comentar
              </button>
            </form>
          ) : null}
        </section>
      </div>

      <BlockModal
        open={blockOpen}
        busy={busy}
        onClose={() => setBlockOpen(false)}
        onConfirm={async (payload) => {
          await runAction(() => api.blockRequest(requestId, payload));
          setBlockOpen(false);
        }}
      />
      <CancelModal
        open={cancelOpen}
        busy={busy}
        onClose={() => setCancelOpen(false)}
        onConfirm={async (justification) => {
          await runAction(() => api.cancelRequest(requestId, justification));
          setCancelOpen(false);
        }}
      />
      <ManualPostModal
        open={manualPostOpen}
        busy={busy}
        onClose={() => setManualPostOpen(false)}
        onConfirm={async () => {
          await runAction(() => api.postManualRequest(requestId));
          setManualPostOpen(false);
        }}
      />
    </div>
  );
}
