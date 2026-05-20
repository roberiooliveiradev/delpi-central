// src/components/notifications/NotificationDispatchHistory.tsx

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  History,
  Pencil,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";

import type {
  CoreApi,
  NotificationCategory,
  NotificationDispatchItem,
  NotificationDispatchRevokedFilter,
  NotificationDispatchStatus,
} from "../../data/coreApi";
import { isEditableScheduledDispatch } from "./dispatchEditForm";
import {
  bulkDeleteConfirmMessage,
  canDeleteDispatch,
  singleDeleteConfirmMessage,
} from "./dispatchHistoryHelpers";
import { NotificationDispatchDetailModal } from "./NotificationDispatchDetailModal";

import "./NotificationDispatchHistory.css";

const PAGE_SIZE = 10;

const STATUS_LABELS: Record<string, string> = {
  pending: "Agendado",
  processing: "Processando",
  completed: "Concluído",
  failed: "Falhou",
};

const STATUS_TABS: { value: NotificationDispatchStatus | ""; label: string }[] = [
  { value: "", label: "Todos" },
  { value: "completed", label: "Concluídos" },
  { value: "pending", label: "Agendados" },
  { value: "failed", label: "Falhou" },
];

const REVOKED_OPTIONS: { value: NotificationDispatchRevokedFilter; label: string }[] = [
  { value: "active", label: "Ativos" },
  { value: "all", label: "Todos" },
  { value: "revoked", label: "Removidos" },
];

const CATEGORY_OPTIONS: { value: NotificationCategory | ""; label: string }[] = [
  { value: "", label: "Todas as categorias" },
  { value: "system", label: "Sistema" },
  { value: "welcome", label: "Boas-vindas" },
  { value: "birthday", label: "Aniversário" },
  { value: "company_event", label: "Evento" },
  { value: "announcement", label: "Comunicado" },
  { value: "custom", label: "Personalizada" },
  { value: "controle_mp", label: "Controle MP" },
];

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
  const [bulkBusy, setBulkBusy] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const [statusFilter, setStatusFilter] = useState<NotificationDispatchStatus | "">("");
  const [categoryFilter, setCategoryFilter] = useState<NotificationCategory | "">("");
  const [revokedFilter, setRevokedFilter] =
    useState<NotificationDispatchRevokedFilter>("active");
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await coreApi.listNotificationDispatches({
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
        search: searchTerm || undefined,
        revoked: revokedFilter,
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
  }, [coreApi, page, statusFilter, categoryFilter, searchTerm, revokedFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setPage(1);
  }, [statusFilter, categoryFilter, searchTerm, revokedFilter]);

  useEffect(() => {
    setSelectedIds([]);
  }, [page, statusFilter, categoryFilter, searchTerm, revokedFilter]);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const selectedCount = selectedIds.length;
  const deletableOnPage = useMemo(() => items.filter(canDeleteDispatch), [items]);
  const allDeletableOnPageSelected =
    deletableOnPage.length > 0 &&
    deletableOnPage.every((item) => selectedSet.has(item.id));

  function toggleSelected(id: string, next: boolean) {
    setSelectedIds((current) => {
      if (next) {
        return current.includes(id) ? current : [...current, id];
      }
      return current.filter((value) => value !== id);
    });
  }

  function toggleSelectAllDeletableOnPage() {
    if (allDeletableOnPageSelected) {
      setSelectedIds([]);
      return;
    }
    setSelectedIds(deletableOnPage.map((item) => item.id));
  }

  function clearSelection() {
    setSelectedIds([]);
  }

  async function handleDeleteDispatch(item: NotificationDispatchItem) {
    if (!canDeleteDispatch(item)) return;
    if (!window.confirm(singleDeleteConfirmMessage(item))) return;

    setDeletingId(item.id);
    setError(null);

    try {
      await coreApi.deleteNotificationDispatch(item.id);
      if (detailDispatchId === item.id) {
        setDetailDispatchId(null);
      }
      setSelectedIds((current) => current.filter((id) => id !== item.id));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir envio");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleBulkDelete() {
    const ids = selectedIds.filter((id) => {
      const item = items.find((row) => row.id === id);
      return item && canDeleteDispatch(item);
    });

    if (!ids.length) return;
    if (!window.confirm(bulkDeleteConfirmMessage(ids.length))) return;

    setBulkBusy(true);
    setError(null);

    try {
      const result = await coreApi.bulkDeleteNotificationDispatches(ids);
      if (result.errors?.length) {
        setError(
          `${result.revoked} revogado(s), ${result.errors.length} com erro.`,
        );
      }
      if (detailDispatchId && ids.includes(detailDispatchId)) {
        setDetailDispatchId(null);
      }
      clearSelection();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir envios");
    } finally {
      setBulkBusy(false);
    }
  }

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

  function applySearch() {
    setSearchTerm(searchInput.trim());
  }

  function clearSearch() {
    setSearchInput("");
    setSearchTerm("");
  }

  const pendingCount = useMemo(
    () => items.filter((item) => item.status === "pending").length,
    [items],
  );

  const summaryLabel = loading
    ? "Carregando…"
    : total === 0
      ? "Nenhum envio"
      : total === 1
        ? "1 envio"
        : `${total} envios`;

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

      <div className="notification-dispatch-history__controls">
        <div
          className="notification-dispatch-history__status-tabs"
          role="tablist"
          aria-label="Status do envio"
        >
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value || "all"}
              type="button"
              role="tab"
              aria-selected={statusFilter === tab.value}
              className={
                statusFilter === tab.value
                  ? "notification-dispatch-history__status-tab notification-dispatch-history__status-tab--active"
                  : "notification-dispatch-history__status-tab"
              }
              onClick={() => setStatusFilter(tab.value)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="notification-dispatch-history__filters">
          <label className="notification-dispatch-history__filter-label">
            <span>Categoria</span>
            <select
              value={categoryFilter}
              onChange={(event) =>
                setCategoryFilter(event.target.value as NotificationCategory | "")
              }
              aria-label="Filtrar por categoria"
            >
              {CATEGORY_OPTIONS.map((option) => (
                <option key={option.value || "all"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="notification-dispatch-history__filter-label">
            <span>Exibição</span>
            <select
              value={revokedFilter}
              onChange={(event) =>
                setRevokedFilter(event.target.value as NotificationDispatchRevokedFilter)
              }
              aria-label="Filtrar por remoção"
            >
              {REVOKED_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <div className="notification-dispatch-history__search">
            <Search size={16} aria-hidden="true" />
            <input
              type="search"
              value={searchInput}
              placeholder="Buscar por título ou template…"
              aria-label="Buscar envios"
              onChange={(event) => setSearchInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  applySearch();
                }
              }}
            />
            {searchInput ? (
              <button
                type="button"
                className="notification-dispatch-history__search-clear"
                aria-label="Limpar busca"
                onClick={clearSearch}
              >
                <X size={14} />
              </button>
            ) : null}
            <button
              type="button"
              className="notification-dispatch-history__search-btn"
              onClick={applySearch}
            >
              Buscar
            </button>
          </div>
        </div>
      </div>

      <div className="notification-dispatch-history__summary-row">
        <p className="notification-dispatch-history__summary" aria-live="polite">
          {summaryLabel}
          {searchTerm ? ` · busca: “${searchTerm}”` : null}
        </p>
        {!loading && deletableOnPage.length > 0 ? (
          <button
            type="button"
            className="notification-dispatch-history__select-page"
            onClick={toggleSelectAllDeletableOnPage}
            disabled={bulkBusy}
          >
            {allDeletableOnPageSelected ? "Desmarcar página" : "Selecionar excluíveis"}
          </button>
        ) : null}
      </div>

      {selectedCount > 0 ? (
        <div className="notification-dispatch-history__bulk" role="region" aria-label="Ações em lote">
          <span className="notification-dispatch-history__bulk-count">
            {selectedCount === 1 ? "1 selecionado" : `${selectedCount} selecionados`}
          </span>
          <div className="notification-dispatch-history__bulk-actions">
            <button
              type="button"
              className="notification-dispatch-history__bulk-btn notification-dispatch-history__bulk-btn--danger"
              disabled={bulkBusy}
              onClick={() => void handleBulkDelete()}
            >
              <Trash2 size={14} aria-hidden="true" />
              {bulkBusy ? "Excluindo…" : "Excluir selecionados"}
            </button>
            <button
              type="button"
              className="notification-dispatch-history__bulk-btn notification-dispatch-history__bulk-btn--ghost"
              disabled={bulkBusy}
              onClick={clearSelection}
            >
              Limpar seleção
            </button>
          </div>
        </div>
      ) : null}

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
        <div className="notification-dispatch-history__empty">Nenhum envio encontrado.</div>
      ) : (
        <div className="notification-dispatch-history__table-wrap">
          <table className="notification-dispatch-history__table">
            <thead>
              <tr>
                <th className="notification-dispatch-history__col-check" aria-label="Selecionar" />
                <th>Data</th>
                <th>Status</th>
                <th>Título / template</th>
                <th>Destinatários</th>
                <th>Formato</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const deletable = canDeleteDispatch(item);
                const selected = selectedSet.has(item.id);

                return (
                  <tr key={item.id} className={selected ? "notification-dispatch-history__row--selected" : undefined}>
                    <td className="notification-dispatch-history__col-check">
                      {deletable ? (
                        <input
                          type="checkbox"
                          checked={selected}
                          disabled={bulkBusy || deletingId === item.id}
                          aria-label={`Selecionar envio ${item.title || item.id}`}
                          onChange={(event) => toggleSelected(item.id, event.target.checked)}
                        />
                      ) : null}
                    </td>
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
                        <small className="notification-dispatch-history__fail">
                          {item.errorMessage}
                        </small>
                      ) : null}
                    </td>
                    <td>
                      <strong>{item.title || item.templateId || "—"}</strong>
                      {item.broadcast ? <small>Broadcast</small> : null}
                    </td>
                    <td>
                      {item.revokedAt
                        ? "Removido"
                        : item.status === "completed"
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
                        {deletable ? (
                          <button
                            type="button"
                            className="notification-dispatch-history__edit notification-dispatch-history__edit--danger"
                            disabled={deletingId === item.id || bulkBusy}
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
                );
              })}
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
