// src/ui/NotificationsPage.tsx

import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  Bell,
  Check,
  ChevronLeft,
  ChevronRight,
  Settings2,
  Star,
  Trash2,
  X,
} from "lucide-react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import {
  CoreApi,
  type NotificationCategory,
  type NotificationHistoryStatus,
  type NotificationItem,
} from "../data/coreApi";
import { NotificationCard } from "../components/notifications/NotificationCard";
import { useNotificationActions } from "../components/notifications/useNotificationActions";
import { NotificationPreferencesPanel } from "../components/notifications/NotificationPreferencesPanel";
import { useNotificationCatalog } from "../state/NotificationCatalogContext";
import {
  buildNotificationCategoryOptions,
  getNotificationCategoryLabel,
} from "../utils/notificationCatalog";

import {
  Alert,
  Button,
  FormField,
  SearchInput,
  SegmentedControl,
  Select,
  Spinner,
  Tabs,
} from "../ui-kit";

import "./NotificationsPage.css";

const PAGE_SIZE = 12;

type PageSection = "inbox" | "preferences";

const SECTION_TABS: { value: PageSection; label: string }[] = [
  { value: "inbox", label: "Histórico" },
  { value: "preferences", label: "Preferências" },
];

const STATUS_TABS: { value: NotificationHistoryStatus; label: string }[] = [
  { value: "all", label: "Todas" },
  { value: "unread", label: "Não lidas" },
  { value: "read", label: "Lidas" },
];

export function NotificationsPage() {
  const { catalog } = useNotificationCatalog();
  const categoryOptions = useMemo(
    () => buildNotificationCategoryOptions(catalog, { includeAll: true }),
    [catalog],
  );
  const {
    getAccessToken,
    refreshToken,
    markAllNotificationsRead,
    reloadNotifications,
  } = useContext(AuthContext);

  const { markNotificationRead, handleDelete, handleToggleImportant, bulkMarkRead, bulkDelete } =
    useNotificationActions();

  const coreApi = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  const [section, setSection] = useState<PageSection>("inbox");
  const [status, setStatus] = useState<NotificationHistoryStatus>("all");
  const [category, setCategory] = useState<NotificationCategory | "">("");
  const [importantOnly, setImportantOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkBusy, setBulkBusy] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearchTerm(searchQuery.trim());
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const offset = (page - 1) * PAGE_SIZE;
      const response = await coreApi.getNotificationHistory({
        status,
        category: category || undefined,
        importantOnly,
        search: searchTerm || undefined,
        limit: PAGE_SIZE,
        offset,
      });
      setItems(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar notificações");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [category, coreApi, importantOnly, page, searchTerm, status]);

  useEffect(() => {
    if (section !== "inbox") {
      return;
    }
    void loadHistory();
  }, [loadHistory, section]);

  useEffect(() => {
    setPage(1);
  }, [status, category, importantOnly, searchTerm]);

  useEffect(() => {
    setSelectedIds([]);
  }, [page, status, category, importantOnly, searchTerm, section]);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const selectedCount = selectedIds.length;
  const allOnPageSelected =
    items.length > 0 && items.every((item) => selectedSet.has(item.id));
  const selectedUnreadCount = items.filter(
    (item) => selectedSet.has(item.id) && !item.read,
  ).length;

  function toggleSelected(id: string, next: boolean) {
    setSelectedIds((current) => {
      if (next) {
        return current.includes(id) ? current : [...current, id];
      }
      return current.filter((value) => value !== id);
    });
  }

  function toggleSelectAllOnPage() {
    if (allOnPageSelected) {
      setSelectedIds([]);
      return;
    }
    setSelectedIds(items.map((item) => item.id));
  }

  function clearSelection() {
    setSelectedIds([]);
  }

  async function handleBulkMarkRead() {
    const ids = items
      .filter((item) => selectedSet.has(item.id) && !item.read)
      .map((item) => item.id);

    if (!ids.length) return;

    setBulkBusy(true);
    setError(null);

    try {
      await bulkMarkRead(ids);
      await reloadNotifications();
      await loadHistory();
      clearSelection();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao marcar notificações como lidas",
      );
    } finally {
      setBulkBusy(false);
    }
  }

  async function handleBulkDelete() {
    if (!selectedCount) return;

    setBulkBusy(true);
    setError(null);

    try {
      await bulkDelete(selectedIds);
      await reloadNotifications();
      await loadHistory();
      clearSelection();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir notificações");
    } finally {
      setBulkBusy(false);
    }
  }

  async function handleMarkRead(id: string) {
    await markNotificationRead(id);
    await loadHistory();
  }

  async function handleMarkAllRead() {
    await markAllNotificationsRead();
    await loadHistory();
  }

  async function handleDeleteAndReload(id: string) {
    await handleDelete(id);
    await loadHistory();
  }

  async function handleToggleImportantAndReload(id: string, isImportant: boolean) {
    await handleToggleImportant(id, isImportant);
    await loadHistory();
  }

  const unreadOnPage = items.filter((item) => !item.read).length;

  const summaryLabel = loading
    ? "Carregando…"
    : total === 0
      ? "Nenhuma notificação"
      : total === 1
        ? "1 notificação"
        : `${total} notificações`;

  const activeSection = SECTION_TABS.find((tab) => tab.value === section)!;

  return (
    <section className="notifications-page" data-tour="notifications-page">
      <div className="notifications-page__header">
        <div className="notifications-page__header-icon" aria-hidden="true">
          <Bell size={22} />
        </div>
        <div className="notifications-page__header-text">
          <h1>Notificações</h1>
          <p>
            {section === "inbox"
              ? "Consulte, filtre e gerencie o histórico das suas mensagens."
              : "Defina quais tipos de mensagem você deseja receber na plataforma."}
          </p>
        </div>
      </div>

      <Tabs
        className="notifications-page__sections"
        aria-label="Seções da página"
        value={section}
        onChange={(id) => setSection(id as PageSection)}
        items={SECTION_TABS.map((tab) => ({
          id: tab.value,
          label: tab.label,
          icon:
            tab.value === "inbox" ? (
              <Bell size={16} />
            ) : (
              <Settings2 size={16} />
            ),
        }))}
      />

      {section === "inbox" ? (
        <div
          id="notifications-panel-inbox"
          role="tabpanel"
          aria-labelledby="portal-ui-tab-inbox"
          className="notifications-page__panel"
        >
          <div className="notifications-page__controls" data-tour="notifications-filters">
            <div className="notifications-page__controls-row">
              <SegmentedControl
                className="notifications-page__status-tabs"
                aria-label="Status das notificações"
                value={status}
                onChange={setStatus}
                options={STATUS_TABS.map((tab) => ({
                  value: tab.value,
                  label: tab.label,
                }))}
              />

              {status !== "read" && unreadOnPage > 0 ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => void handleMarkAllRead()}
                >
                  Marcar todas como lidas
                </Button>
              ) : null}
            </div>

            <div className="notifications-page__controls-divider" aria-hidden="true" />

            <div className="notifications-page__filters">
              <SearchInput
                className="notifications-page__search"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                onClear={() => setSearchQuery("")}
                placeholder="Buscar por título ou mensagem…"
                aria-label="Buscar no histórico de notificações"
              />

              <FormField
                label="Categoria"
                htmlFor="notifications-page-category"
                className="notifications-page__filter-label"
              >
                <Select
                  id="notifications-page-category"
                  value={category}
                  onChange={(value) =>
                    setCategory(value as NotificationCategory | "")
                  }
                  aria-label="Filtrar por categoria"
                  options={categoryOptions.map((option) => ({
                    value: option.value,
                    label: option.label,
                  }))}
                />
              </FormField>

              <Button
                type="button"
                variant="secondary"
                size="sm"
                pressed={importantOnly}
                icon={<Star size={14} />}
                onClick={() => setImportantOnly((current) => !current)}
              >
                Importantes
              </Button>
            </div>
          </div>

          <div className="notifications-page__summary-row">
            <p className="notifications-page__summary" aria-live="polite">
              {summaryLabel}
              {!loading && status === "unread" ? " · não lidas" : null}
              {!loading && status === "read" ? " · lidas" : null}
              {!loading && importantOnly ? " · importantes" : null}
              {!loading && category
                ? ` · ${getNotificationCategoryLabel(category, catalog)}`
                : null}
              {!loading && searchTerm ? ` · busca: «${searchTerm}»` : null}
            </p>

            {!loading && items.length > 0 ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={toggleSelectAllOnPage}
                disabled={bulkBusy}
              >
                {allOnPageSelected ? "Desmarcar página" : "Selecionar página"}
              </Button>
            ) : null}
          </div>

          {selectedCount > 0 ? (
            <div className="notifications-page__bulk" role="region" aria-label="Ações em lote">
              <span className="notifications-page__bulk-count">
                {selectedCount === 1
                  ? "1 selecionada"
                  : `${selectedCount} selecionadas`}
              </span>

              <div className="notifications-page__bulk-actions">
                {selectedUnreadCount > 0 ? (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    disabled={bulkBusy}
                    icon={<Check size={16} />}
                    onClick={() => void handleBulkMarkRead()}
                  >
                    Marcar como lidas
                  </Button>
                ) : null}

                <Button
                  type="button"
                  variant="danger-soft"
                  size="sm"
                  disabled={bulkBusy}
                  icon={<Trash2 size={16} />}
                  onClick={() => void handleBulkDelete()}
                >
                  Excluir
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={bulkBusy}
                  onClick={clearSelection}
                  aria-label="Limpar seleção"
                  icon={<X size={16} />}
                >
                  Limpar
                </Button>
              </div>
            </div>
          ) : null}

          {error ? <Alert tone="danger">{error}</Alert> : null}

          <div className="notifications-page__feed">
            {loading ? (
              <Spinner label="Carregando notificações…" />
            ) : items.length === 0 ? (
              <div className="notifications-page__empty">
                <Bell size={32} aria-hidden="true" strokeWidth={1.5} />
                <p>
                  {searchTerm
                    ? `Nenhuma notificação encontrada para «${searchTerm}».`
                    : "Nenhuma notificação neste filtro."}
                </p>
              </div>
            ) : (
              <ul className="notifications-page__list" data-tour="notifications-list">
                {items.map((notification) => (
                  <li key={notification.id}>
                    <NotificationCard
                      variant="page"
                      notification={notification}
                      selectionEnabled
                      selected={selectedSet.has(notification.id)}
                      onSelectedChange={(next) => toggleSelected(notification.id, next)}
                      onMarkRead={handleMarkRead}
                      onDelete={(id) => void handleDeleteAndReload(id)}
                      onToggleImportant={(id, isImportant) =>
                        void handleToggleImportantAndReload(id, isImportant)
                      }
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>

          {totalPages > 1 ? (
            <footer className="notifications-page__pagination">
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
                Página {page} de {totalPages} · {total} no total
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
        </div>
      ) : (
        <div
          id="notifications-panel-preferences"
          role="tabpanel"
          aria-labelledby="portal-ui-tab-preferences"
          className="notifications-page__panel notifications-page__panel--preferences"
        >
          <div data-tour="notifications-preferences">
            <NotificationPreferencesPanel
              variant="page"
              coreApi={coreApi}
              onSaved={() => void reloadNotifications()}
            />
          </div>
        </div>
      )}

      <span className="visually-hidden" aria-live="polite">
        Seção ativa: {activeSection.label}
      </span>
    </section>
  );
}
