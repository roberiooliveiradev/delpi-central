// src/components/notifications/NotificationDispatchHistory.tsx

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Eye, History, Pencil, RefreshCw, Trash2 } from "lucide-react";

import type { CoreApi, NotificationDispatchItem } from "../../data/coreApi";
import { isEditableScheduledDispatch } from "./dispatchEditForm";
import { NotificationDispatchDetailModal } from "./NotificationDispatchDetailModal";

import "./NotificationDispatchHistory.css";

const PAGE_SIZE = 10;

const STATUS_LABELS: Record<string, string> = {
  pending: "Agendado",
  processing: "Processando",
  completed: "Concluído",
  failed: "Falhou",
};

type NotificationDispatchHistoryProps = {
  coreApi: CoreApi;
  onEditDispatch?: (dispatchId: string) => void;
};

export function NotificationDispatchHistory({
  coreApi,
  onEditDispatch,
}: NotificationDispatchHistoryProps) {
  const [items, setItems] = useState<NotificationDispatchItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [detailDispatchId, setDetailDispatchId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function canDeleteDispatch(item: NotificationDispatchItem) {
    if (item.revokedAt) return false;
    if (item.status === "pending") return true;
    if (item.status === "processing") return false;
    return item.createdCount > 0 || item.status === "completed";
  }

  function deleteConfirmMessage(item: NotificationDispatchItem) {
    if (item.status === "pending") {
      return "Cancelar este envio agendado? Ele será removido do histórico.";
    }
    const count = item.createdCount > 0 ? item.createdCount : "todos os";
    return `Excluir este envio para ${count} destinatário(s)? A notificação sumirá da caixa de entrada de quem recebeu.`;
  }

  async function handleDeleteDispatch(item: NotificationDispatchItem) {
    if (!canDeleteDispatch(item)) return;
    if (!window.confirm(deleteConfirmMessage(item))) return;

    setDeletingId(item.id);
    setError(null);

    try {
      await coreApi.deleteNotificationDispatch(item.id);
      if (detailDispatchId === item.id) {
        setDetailDispatchId(null);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir envio");
    } finally {
      setDeletingId(null);
    }
  }

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await coreApi.listNotificationDispatches({
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      });
      setItems(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar histórico");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [coreApi, page]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleProcessPending() {
    setProcessing(true);
    setError(null);

    try {
      const result = await coreApi.processPendingNotificationDispatches({ limit: 20 });
      setError(
        result.failed > 0
          ? `Processados: ${result.completed} ok, ${result.failed} com erro.`
          : null,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao processar agendados");
    } finally {
      setProcessing(false);
    }
  }

  const pendingCount = useMemo(
    () => items.filter((item) => item.status === "pending").length,
    [items],
  );

  return (
    <section className="notification-dispatch-history">
      <header className="notification-dispatch-history__head">
        <div>
          <h3 className="admin-notifications__panel-title">
            <History size={18} aria-hidden="true" /> Histórico de envios
          </h3>
          <p className="admin-notifications__panel-desc">
            Auditoria de campanhas enviadas ou agendadas pela plataforma.
          </p>
        </div>
        <div className="notification-dispatch-history__actions">
          <button
            type="button"
            className="notification-dispatch-history__btn"
            onClick={() => void load()}
            disabled={loading}
          >
            <RefreshCw size={16} aria-hidden="true" />
            Atualizar
          </button>
          <button
            type="button"
            className="notification-dispatch-history__btn notification-dispatch-history__btn--primary"
            onClick={() => void handleProcessPending()}
            disabled={processing}
          >
            {processing ? "Processando…" : "Processar agendados"}
          </button>
        </div>
      </header>

      {pendingCount > 0 ? (
        <p className="notification-dispatch-history__hint">
          {pendingCount} envio(s) agendado(s) nesta página. A Core API processa automaticamente no
          horário (verificação periódica). Use “Processar agendados” apenas para forçar agora.
        </p>
      ) : null}

      {error ? <p className="notification-dispatch-history__error">{error}</p> : null}

      {loading ? (
        <p className="notification-dispatch-history__loading">Carregando…</p>
      ) : items.length === 0 ? (
        <div className="notification-dispatch-history__empty">Nenhum envio registrado ainda.</div>
      ) : (
        <div className="notification-dispatch-history__table-wrap">
          <table className="notification-dispatch-history__table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Status</th>
                <th>Título / template</th>
                <th>Destinatários</th>
                <th>Formato</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <time dateTime={item.createdAt}>
                      {new Date(item.createdAt).toLocaleString("pt-BR")}
                    </time>
                    {item.scheduledAt ? (
                      <small>
                        Agendado: {new Date(item.scheduledAt).toLocaleString("pt-BR")}
                      </small>
                    ) : null}
                  </td>
                  <td>
                    <span
                      className={`notification-dispatch-history__status notification-dispatch-history__status--${item.status}`}
                    >
                      {STATUS_LABELS[item.status] ?? item.status}
                    </span>
                    {item.errorMessage ? (
                      <small className="notification-dispatch-history__fail">{item.errorMessage}</small>
                    ) : null}
                  </td>
                  <td>
                    <strong>{item.title || item.templateId || "—"}</strong>
                    {item.broadcast ? <small>Broadcast</small> : null}
                  </td>
                  <td>
                    {item.status === "completed"
                      ? `${item.createdCount} criada(s)`
                      : item.status === "pending"
                        ? "—"
                        : `${item.createdCount}`}
                  </td>
                  <td>{item.presentation}</td>
                  <td>
                    <div className="notification-dispatch-history__row-actions">
                      <button
                        type="button"
                        className="notification-dispatch-history__edit"
                        onClick={() => setDetailDispatchId(item.id)}
                      >
                        <Eye size={14} aria-hidden="true" />
                        Detalhes
                      </button>
                      {onEditDispatch &&
                      isEditableScheduledDispatch(item.status, item.scheduledAt) ? (
                        <button
                          type="button"
                          className="notification-dispatch-history__edit"
                          onClick={() => onEditDispatch(item.id)}
                        >
                          <Pencil size={14} aria-hidden="true" />
                          Editar
                        </button>
                      ) : null}
                      {canDeleteDispatch(item) ? (
                        <button
                          type="button"
                          className="notification-dispatch-history__edit notification-dispatch-history__edit--danger"
                          disabled={deletingId === item.id}
                          onClick={() => void handleDeleteDispatch(item)}
                        >
                          <Trash2 size={14} aria-hidden="true" />
                          {deletingId === item.id ? "Excluindo…" : "Excluir"}
                        </button>
                      ) : item.revokedAt ? (
                        <span className="notification-dispatch-history__muted">Removido</span>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 ? (
        <footer className="notification-dispatch-history__pagination">
          <button
            type="button"
            disabled={page <= 1 || loading}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            aria-label="Página anterior"
          >
            <ChevronLeft size={18} />
          </button>
          <span>
            Página {page} de {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            aria-label="Próxima página"
          >
            <ChevronRight size={18} />
          </button>
        </footer>
      ) : null}

      <NotificationDispatchDetailModal
        open={detailDispatchId != null}
        dispatchId={detailDispatchId}
        coreApi={coreApi}
        onClose={() => setDetailDispatchId(null)}
        onDeleted={() => {
          setDetailDispatchId(null);
          void load();
        }}
      />
    </section>
  );
}
