// src/components/notifications/NotificationDispatchHistory.tsx

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  History,
  Pencil,
  RefreshCw,
  Trash2,
} from "lucide-react";

import type {
  CoreApi,
  NotificationCategory,
  NotificationDispatchItem,
  NotificationDispatchRevokedFilter,
  NotificationDispatchStatus,
} from "../../data/coreApi";
import { useConfirmDialog } from "../ConfirmDialogProvider";
import { isEditableScheduledDispatch } from "./dispatchEditForm";
import {
  bulkDeleteConfirmMessage,
  canDeleteDispatch,
  singleDeleteConfirmMessage,
} from "./dispatchHistoryHelpers";
import { NotificationDispatchDetailModal } from "./NotificationDispatchDetailModal";
import { useNotificationCatalog } from "../../state/NotificationCatalogContext";
import { buildNotificationCategoryOptions } from "../../utils/notificationCatalog";
import {
  Alert,
  Button,
  Checkbox,
  FormField,
  SearchInput,
  SegmentedControl,
  Select,
  Spinner,
} from "../../ui-kit";

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

type NotificationDispatchHistoryProps = {
  coreApi: CoreApi;
  onEditDispatch?: (dispatchId: string) => void;
};

export function NotificationDispatchHistory({
  coreApi,
  onEditDispatch,
}: NotificationDispatchHistoryProps) {
  const confirm = useConfirmDialog();
  const { catalog } = useNotificationCatalog();
  const categoryOptions = useMemo(
    () => buildNotificationCategoryOptions(catalog, { includeAll: true }),
    [catalog],
  );
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
    const confirmed = await confirm({
      title: "Excluir envio",
      message: singleDeleteConfirmMessage(item),
      confirmText: "Excluir",
      danger: true,
    });
    if (!confirmed) return;

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
    const confirmed = await confirm({
      title: "Excluir envios",
      message: bulkDeleteConfirmMessage(ids.length),
      confirmText: "Excluir",
      danger: true,
    });
    if (!confirmed) return;

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
          <Button
            type="button"
            variant="secondary"
            icon={<RefreshCw size={16} />}
            onClick={() => void load()}
            disabled={loading}
          >
            Atualizar
          </Button>
          <Button
            type="button"
            variant="primary"
            loading={processing}
            onClick={() => void handleProcessPending()}
            disabled={processing}
          >
            {processing ? "Processando…" : "Processar agendados"}
          </Button>
        </div>
      </header>

      <div className="notification-dispatch-history__controls">
        <SegmentedControl
          className="notification-dispatch-history__status-tabs"
          aria-label="Status do envio"
          value={statusFilter}
          onChange={setStatusFilter}
          options={STATUS_TABS.map((tab) => ({
            value: tab.value,
            label: tab.label,
          }))}
        />

        <div className="notification-dispatch-history__filters">
          <FormField
            label="Categoria"
            htmlFor="dispatch-history-category"
            className="notification-dispatch-history__filter-label"
          >
            <Select
              id="dispatch-history-category"
              value={categoryFilter}
              onChange={(value) =>
                setCategoryFilter(value as NotificationCategory | "")
              }
              aria-label="Filtrar por categoria"
              options={categoryOptions.map((option) => ({
                value: option.value,
                label: option.label,
              }))}
            />
          </FormField>

          <FormField
            label="Exibição"
            htmlFor="dispatch-history-revoked"
            className="notification-dispatch-history__filter-label"
          >
            <Select
              id="dispatch-history-revoked"
              value={revokedFilter}
              onChange={(value) =>
                setRevokedFilter(value as NotificationDispatchRevokedFilter)
              }
              aria-label="Filtrar por remoção"
              options={REVOKED_OPTIONS.map((option) => ({
                value: option.value,
                label: option.label,
              }))}
            />
          </FormField>

          <div className="notification-dispatch-history__search">
            <SearchInput
              value={searchInput}
              placeholder="Buscar por título ou template…"
              aria-label="Buscar envios"
              onChange={(event) => setSearchInput(event.target.value)}
              onClear={clearSearch}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  applySearch();
                }
              }}
            />
            <Button type="button" variant="secondary" onClick={applySearch}>
              Buscar
            </Button>
          </div>
        </div>
      </div>

      <div className="notification-dispatch-history__summary-row">
        <p className="notification-dispatch-history__summary" aria-live="polite">
          {summaryLabel}
          {searchTerm ? ` · busca: “${searchTerm}”` : null}
        </p>
        {!loading && deletableOnPage.length > 0 ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={toggleSelectAllDeletableOnPage}
            disabled={bulkBusy}
          >
            {allDeletableOnPageSelected ? "Desmarcar página" : "Selecionar excluíveis"}
          </Button>
        ) : null}
      </div>

      {selectedCount > 0 ? (
        <div className="notification-dispatch-history__bulk" role="region" aria-label="Ações em lote">
          <span className="notification-dispatch-history__bulk-count">
            {selectedCount === 1 ? "1 selecionado" : `${selectedCount} selecionados`}
          </span>
          <div className="notification-dispatch-history__bulk-actions">
            <Button
              type="button"
              variant="danger-soft"
              size="sm"
              disabled={bulkBusy}
              loading={bulkBusy}
              icon={<Trash2 size={14} />}
              onClick={() => void handleBulkDelete()}
            >
              {bulkBusy ? "Excluindo…" : "Excluir selecionados"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={bulkBusy}
              onClick={clearSelection}
            >
              Limpar seleção
            </Button>
          </div>
        </div>
      ) : null}

      {pendingCount > 0 ? (
        <p className="notification-dispatch-history__hint">
          {pendingCount} envio(s) agendado(s) nesta página. A Core API processa automaticamente no
          horário (verificação periódica). Use “Processar agendados” apenas para forçar agora.
        </p>
      ) : null}

      {error ? <Alert tone="danger">{error}</Alert> : null}

      {loading ? (
        <Spinner label="Carregando…" />
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
                        <Checkbox
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
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          icon={<Eye size={14} />}
                          onClick={() => setDetailDispatchId(item.id)}
                        >
                          Detalhes
                        </Button>
                        {onEditDispatch &&
                        isEditableScheduledDispatch(item.status, item.scheduledAt) ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            icon={<Pencil size={14} />}
                            onClick={() => onEditDispatch(item.id)}
                          >
                            Editar
                          </Button>
                        ) : null}
                        {deletable ? (
                          <Button
                            type="button"
                            variant="danger-soft"
                            size="sm"
                            disabled={deletingId === item.id || bulkBusy}
                            loading={deletingId === item.id}
                            icon={<Trash2 size={14} />}
                            onClick={() => void handleDeleteDispatch(item)}
                          >
                            {deletingId === item.id ? "Excluindo…" : "Excluir"}
                          </Button>
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
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={page <= 1 || loading}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            aria-label="Página anterior"
            icon={<ChevronLeft size={18} />}
          />
          <span>
            Página {page} de {totalPages}
          </span>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            aria-label="Próxima página"
            icon={<ChevronRight size={18} />}
          />
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
