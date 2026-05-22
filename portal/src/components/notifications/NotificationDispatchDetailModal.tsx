// src/components/notifications/NotificationDispatchDetailModal.tsx

import { useEffect, useMemo, useState } from "react";
import { Check, Trash2, X } from "lucide-react";

import { Modal } from "../Modal";
import type {
  CoreApi,
  NotificationCategory,
  NotificationDispatchDetail,
  NotificationDispatchRecipient,
} from "../../data/coreApi";
import { canDeleteDispatch, singleDeleteConfirmMessage } from "./dispatchHistoryHelpers";

import "./NotificationDispatchDetailModal.css";

const STATUS_LABELS: Record<string, string> = {
  pending: "Agendado",
  processing: "Processando",
  completed: "Concluído",
  failed: "Falhou",
};

const CATEGORY_LABELS: Record<NotificationCategory, string> = {
  system: "Sistema",
  welcome: "Boas-vindas",
  birthday: "Aniversário",
  company_event: "Evento",
  announcement: "Comunicado",
  custom: "Personalizada",
  controle_mp: "Controle MP",
  transformometro: "Transformômetro",
};

const RECIPIENT_PREVIEW_LIMIT = 80;

type Props = {
  open: boolean;
  dispatchId: string | null;
  coreApi: CoreApi;
  onClose: () => void;
  onDeleted?: () => void;
};

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR");
}

function payloadMessage(payload: Record<string, unknown>) {
  const message = payload.message ?? payload.htmlContent;
  if (typeof message === "string" && message.trim()) {
    return message.length > 500 ? `${message.slice(0, 500)}…` : message;
  }
  return null;
}

function RecipientTable({
  rows,
  showReadStatus = false,
}: {
  rows: NotificationDispatchRecipient[];
  showReadStatus?: boolean;
}) {
  if (rows.length === 0) {
    return <p className="dispatch-detail-modal__empty-list">Nenhum registro.</p>;
  }

  return (
    <div className="dispatch-detail-modal__table-wrap">
      <table className="dispatch-detail-modal__table">
        <thead>
          <tr>
            <th>Nome</th>
            <th>E-mail</th>
            {showReadStatus ? <th>Lida</th> : null}
            {showReadStatus ? <th>Entregue em</th> : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const key = row.notificationId ?? row.id ?? row.userId ?? row.email;
            return (
              <tr key={key}>
                <td>{row.name || "—"}</td>
                <td>{row.email || "—"}</td>
                {showReadStatus ? (
                  <td>
                    {row.read ? (
                      <span className="dispatch-detail-modal__read-yes" title="Lida">
                        <Check size={14} aria-hidden="true" />
                      </span>
                    ) : (
                      <span className="dispatch-detail-modal__read-no" title="Não lida">
                        <X size={14} aria-hidden="true" />
                      </span>
                    )}
                  </td>
                ) : null}
                {showReadStatus ? <td>{formatDateTime(row.createdAt)}</td> : null}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function NotificationDispatchDetailModal({
  open,
  dispatchId,
  coreApi,
  onClose,
  onDeleted,
}: Props) {
  const [detail, setDetail] = useState<NotificationDispatchDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !dispatchId) {
      setDetail(null);
      setError(null);
      return;
    }

    let cancelled = false;

    async function load() {
      if (!dispatchId) return;

      setLoading(true);
      setError(null);

      try {
        const response = await coreApi.getNotificationDispatch(dispatchId);
        if (!cancelled) {
          setDetail(response);
        }
      } catch (err) {
        if (!cancelled) {
          setDetail(null);
          setError(err instanceof Error ? err.message : "Falha ao carregar detalhes");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [open, dispatchId, coreApi]);

  const intendedPreview = useMemo(() => {
    if (!detail) return { rows: [], truncated: 0 };
    const rows = detail.intendedRecipients ?? [];
    if (rows.length <= RECIPIENT_PREVIEW_LIMIT) {
      return { rows, truncated: 0 };
    }
    return {
      rows: rows.slice(0, RECIPIENT_PREVIEW_LIMIT),
      truncated: rows.length - RECIPIENT_PREVIEW_LIMIT,
    };
  }, [detail]);

  const delivered = detail?.deliveredRecipients ?? [];
  const targeting = detail?.targeting;
  const messagePreview = detail ? payloadMessage(detail.payload) : null;

  async function handleDelete() {
    if (!detail || !canDeleteDispatch(detail)) return;
    if (!window.confirm(singleDeleteConfirmMessage(detail))) return;

    setDeleting(true);
    setError(null);

    try {
      await coreApi.deleteNotificationDispatch(detail.id);
      onDeleted?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir envio");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Modal
      open={open}
      title="Detalhes do envio"
      onClose={onClose}
      size="xl"
      footer={
        <div className="dispatch-detail-modal__footer">
          {detail && canDeleteDispatch(detail) ? (
            <button
              type="button"
              className="dispatch-detail-modal__delete-btn"
              disabled={deleting}
              onClick={() => void handleDelete()}
            >
              <Trash2 size={16} aria-hidden="true" />
              {deleting ? "Excluindo…" : "Excluir para todos"}
            </button>
          ) : detail?.revokedAt ? (
            <span className="dispatch-detail-modal__revoked">
              Removido em {formatDateTime(detail.revokedAt)}
            </span>
          ) : null}
          <button type="button" className="dispatch-detail-modal__close-btn" onClick={onClose}>
            Fechar
          </button>
        </div>
      }
    >
      {loading ? <p className="dispatch-detail-modal__loading">Carregando detalhes…</p> : null}
      {error ? <p className="dispatch-detail-modal__error">{error}</p> : null}

      {!loading && !error && detail ? (
        <div className="dispatch-detail-modal">
          <section className="dispatch-detail-modal__section">
            <h4>Resumo</h4>
            <dl className="dispatch-detail-modal__grid">
              <div>
                <dt>Status</dt>
                <dd>
                  <span
                    className={`dispatch-detail-modal__status dispatch-detail-modal__status--${detail.status}`}
                  >
                    {STATUS_LABELS[detail.status] ?? detail.status}
                  </span>
                </dd>
              </div>
              <div>
                <dt>Título</dt>
                <dd>{detail.title || detail.templateId || "—"}</dd>
              </div>
              <div>
                <dt>Categoria</dt>
                <dd>{CATEGORY_LABELS[detail.category] ?? detail.category}</dd>
              </div>
              <div>
                <dt>Formato</dt>
                <dd>{detail.presentation}</dd>
              </div>
              <div>
                <dt>Criado em</dt>
                <dd>{formatDateTime(detail.createdAt)}</dd>
              </div>
              <div>
                <dt>Processado em</dt>
                <dd>{formatDateTime(detail.processedAt)}</dd>
              </div>
              {detail.scheduledAt ? (
                <div>
                  <dt>Agendado para</dt>
                  <dd>{formatDateTime(detail.scheduledAt)}</dd>
                </div>
              ) : null}
              <div>
                <dt>Planejados</dt>
                <dd>{detail.recipientCount}</dd>
              </div>
              <div>
                <dt>Notificações criadas</dt>
                <dd>{detail.createdCount}</dd>
              </div>
              {detail.eligibleRecipientCount != null ? (
                <div>
                  <dt>Elegíveis (acesso ao app)</dt>
                  <dd>{detail.eligibleRecipientCount}</dd>
                </div>
              ) : null}
              {detail.sourceApp ? (
                <div>
                  <dt>App de origem</dt>
                  <dd>
                    <code>{detail.sourceApp}</code>
                  </dd>
                </div>
              ) : null}
              {detail.createdBy ? (
                <div>
                  <dt>Enviado por</dt>
                  <dd>
                    {detail.createdBy.name} ({detail.createdBy.email})
                  </dd>
                </div>
              ) : null}
            </dl>
            {detail.errorMessage ? (
              <p className="dispatch-detail-modal__error">{detail.errorMessage}</p>
            ) : null}
            {messagePreview ? (
              <div className="dispatch-detail-modal__message">
                <strong>Mensagem</strong>
                <p>{messagePreview}</p>
              </div>
            ) : null}
          </section>

          {targeting ? (
            <section className="dispatch-detail-modal__section">
              <h4>Segmentação do envio</h4>
              <dl className="dispatch-detail-modal__grid">
                <div>
                  <dt>Broadcast</dt>
                  <dd>{targeting.broadcast ? "Sim" : "Não"}</dd>
                </div>
                {targeting.userIds.length > 0 ? (
                  <div>
                    <dt>Usuários (IDs)</dt>
                    <dd>{targeting.userIds.length} selecionado(s)</dd>
                  </div>
                ) : null}
                {targeting.emails.length > 0 ? (
                  <div>
                    <dt>E-mails extras</dt>
                    <dd>{targeting.emails.join(", ")}</dd>
                  </div>
                ) : null}
                {targeting.roleIds.length > 0 ? (
                  <div>
                    <dt>Perfis</dt>
                    <dd>{targeting.roleIds.length} perfil(is)</dd>
                  </div>
                ) : null}
                {targeting.groupIds.length > 0 ? (
                  <div>
                    <dt>Grupos</dt>
                    <dd>{targeting.groupIds.length} grupo(s)</dd>
                  </div>
                ) : null}
                {targeting.excludedUserIds.length > 0 ? (
                  <div>
                    <dt>Excluídos</dt>
                    <dd>{targeting.excludedUserIds.length} usuário(s)</dd>
                  </div>
                ) : null}
                {targeting.actionType ? (
                  <div>
                    <dt>Ação</dt>
                    <dd>
                      {targeting.actionLabel || targeting.actionType}
                      {targeting.actionTarget ? (
                        <>
                          {" "}
                          → <code>{targeting.actionTarget}</code>
                        </>
                      ) : null}
                    </dd>
                  </div>
                ) : null}
              </dl>
            </section>
          ) : null}

          <section className="dispatch-detail-modal__section">
            <h4>
              Quem recebeu ({delivered.length})
            </h4>
            <p className="dispatch-detail-modal__hint">
              Lista das notificações efetivamente criadas na caixa de entrada dos usuários.
            </p>
            <RecipientTable rows={delivered} showReadStatus />
          </section>

          <section className="dispatch-detail-modal__section">
            <h4>
              Destinatários planejados ({detail.intendedRecipients.length})
            </h4>
            <p className="dispatch-detail-modal__hint">
              Resolução atual do payload (perfis, grupos, broadcast). Pode diferir do entregue por
              preferências, RBAC ou filtro de acesso ao app.
            </p>
            <RecipientTable rows={intendedPreview.rows} />
            {intendedPreview.truncated > 0 ? (
              <p className="dispatch-detail-modal__hint">
                Exibindo os primeiros {RECIPIENT_PREVIEW_LIMIT}. Mais{" "}
                {intendedPreview.truncated} destinatário(s) não listados.
              </p>
            ) : null}
          </section>
        </div>
      ) : null}
    </Modal>
  );
}
