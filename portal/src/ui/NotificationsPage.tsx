// src/ui/NotificationsPage.tsx

import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Bell, ChevronLeft, ChevronRight, Star } from "lucide-react";
import { useNavigate } from "react-router-dom";

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

import "./NotificationsPage.css";

const PAGE_SIZE = 12;

const STATUS_TABS: { value: NotificationHistoryStatus; label: string }[] = [
  { value: "all", label: "Todas" },
  { value: "unread", label: "Não lidas" },
  { value: "read", label: "Lidas" },
];

const CATEGORY_OPTIONS: { value: NotificationCategory | ""; label: string }[] = [
  { value: "", label: "Todas as categorias" },
  { value: "system", label: "Sistema" },
  { value: "welcome", label: "Boas-vindas" },
  { value: "birthday", label: "Aniversário" },
  { value: "company_event", label: "Evento" },
  { value: "announcement", label: "Comunicado" },
  { value: "custom", label: "Personalizada" },
];

export function NotificationsPage() {
  const navigate = useNavigate();
  const {
    getAccessToken,
    refreshToken,
    markAllNotificationsRead,
    reloadNotifications,
  } = useContext(AuthContext);

  const { markNotificationRead, handleDelete, handleToggleImportant } = useNotificationActions();

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

  const [status, setStatus] = useState<NotificationHistoryStatus>("all");
  const [category, setCategory] = useState<NotificationCategory | "">("");
  const [importantOnly, setImportantOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const offset = (page - 1) * PAGE_SIZE;
      const response = await coreApi.getNotificationHistory({
        status,
        category: category || undefined,
        importantOnly,
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
  }, [category, coreApi, importantOnly, page, status]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    setPage(1);
  }, [status, category, importantOnly]);

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

  return (
    <section className="notifications-page">
      <header className="notifications-page__header">
        <div className="notifications-page__header-icon" aria-hidden="true">
          <Bell size={22} />
        </div>
        <div>
          <h1>Notificações</h1>
          <p>Histórico completo das suas mensagens na plataforma.</p>
        </div>
      </header>

      <NotificationPreferencesPanel
        coreApi={coreApi}
        onSaved={() => void reloadNotifications()}
      />

      <div className="notifications-page__toolbar">
        <div className="notifications-page__tabs" role="tablist" aria-label="Filtro">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={status === tab.value}
              className={
                status === tab.value
                  ? "notifications-page__tab notifications-page__tab--active"
                  : "notifications-page__tab"
              }
              onClick={() => setStatus(tab.value)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {status !== "read" && unreadOnPage > 0 ? (
          <button
            type="button"
            className="notifications-page__mark-all"
            onClick={() => void handleMarkAllRead()}
          >
            Marcar todas como lidas
          </button>
        ) : null}
      </div>

      <div className="notifications-page__filters">
        <label className="notifications-page__filter-label">
          <span className="notifications-page__filter-text">Categoria</span>
          <select
            className="notifications-page__select"
            value={category}
            onChange={(event) => setCategory(event.target.value as NotificationCategory | "")}
            aria-label="Filtrar por categoria"
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className={
            importantOnly
              ? "notifications-page__important-toggle notifications-page__important-toggle--active"
              : "notifications-page__important-toggle"
          }
          aria-pressed={importantOnly}
          onClick={() => setImportantOnly((current) => !current)}
        >
          <Star size={14} aria-hidden="true" />
          Importantes
        </button>
      </div>

      <p className="notifications-page__summary" aria-live="polite">
        {summaryLabel}
        {!loading && status === "unread" ? " · não lidas" : null}
        {!loading && status === "read" ? " · lidas" : null}
        {!loading && importantOnly ? " · importantes" : null}
        {!loading && category ? ` · ${CATEGORY_OPTIONS.find((o) => o.value === category)?.label ?? category}` : null}
      </p>

      {error ? <p className="notifications-page__error">{error}</p> : null}

      <div className="notifications-page__feed">
        {loading ? (
          <p className="notifications-page__loading">Carregando notificações…</p>
        ) : items.length === 0 ? (
          <div className="notifications-page__empty">
            <Bell size={32} aria-hidden="true" strokeWidth={1.5} />
            <p>Nenhuma notificação neste filtro.</p>
          </div>
        ) : (
          <ul className="notifications-page__list">
            {items.map((notification) => (
              <li key={notification.id}>
                <NotificationCard
                  variant="page"
                  notification={notification}
                  onMarkRead={handleMarkRead}
                  onDelete={(id) => void handleDeleteAndReload(id)}
                  onToggleImportant={(id, isImportant) =>
                    void handleToggleImportantAndReload(id, isImportant)
                  }
                  onNavigate={
                    notification.action?.type === "portal_route"
                      ? () => navigate(notification.action!.target)
                      : undefined
                  }
                />
              </li>
            ))}
          </ul>
        )}
      </div>

      {totalPages > 1 ? (
        <footer className="notifications-page__pagination">
          <button
            type="button"
            disabled={page <= 1 || loading}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            aria-label="Página anterior"
          >
            <ChevronLeft size={18} />
          </button>
          <span>
            Página {page} de {totalPages} · {total} no total
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
    </section>
  );
}
