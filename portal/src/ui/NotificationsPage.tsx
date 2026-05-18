// src/ui/NotificationsPage.tsx

import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Bell, ChevronLeft, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi, type NotificationHistoryStatus, type NotificationItem } from "../data/coreApi";
import { NotificationCard } from "../components/notifications/NotificationCard";

import "./NotificationsPage.css";

const PAGE_SIZE = 12;

const STATUS_TABS: { value: NotificationHistoryStatus; label: string }[] = [
  { value: "all", label: "Todas" },
  { value: "unread", label: "Não lidas" },
  { value: "read", label: "Lidas" },
];

export function NotificationsPage() {
  const navigate = useNavigate();
  const { getAccessToken, refreshToken, markNotificationRead, markAllNotificationsRead } =
    useContext(AuthContext);

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
  }, [coreApi, page, status]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    setPage(1);
  }, [status]);

  async function handleMarkRead(id: string) {
    await markNotificationRead(id);
    await loadHistory();
  }

  async function handleMarkAllRead() {
    await markAllNotificationsRead();
    await loadHistory();
  }

  const unreadOnPage = items.filter((item) => !item.read).length;

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

      {error ? <p className="notifications-page__error">{error}</p> : null}

      {loading ? (
        <p className="notifications-page__loading">Carregando…</p>
      ) : items.length === 0 ? (
        <div className="notifications-page__empty">
          <Bell size={28} aria-hidden="true" />
          <p>Nenhuma notificação neste filtro.</p>
        </div>
      ) : (
        <ul className="notifications-page__list">
          {items.map((notification) => (
            <li key={notification.id}>
              <NotificationCard
                notification={notification}
                onMarkRead={handleMarkRead}
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
