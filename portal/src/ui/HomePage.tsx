// src/ui/HomePage.tsx

import { useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { getRecentAppIds } from "../utils/recentApps";
import { AppLauncherCard } from "../components/AppLauncherCard";
import { NotificationCard } from "../components/notifications/NotificationCard";
import { useNotificationActions } from "../components/notifications/useNotificationActions";
import {
  Bell,
  Star,
  Shield,
  ArrowRight,
  Activity,
} from "lucide-react";

import { motion } from "framer-motion";
import { useRoutesByApp } from "../hooks/useRoutesByApp";
import { useAppsById } from "../hooks/useAppsById";
import { isLaunchableApp } from "../utils/launchableApps";
import { PortalTourHomeEntry } from "../tour/PortalTourHomeEntry";

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

const fadeUp = {
  hidden: { opacity: 0, y: 10 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.22, delay: 0.04 * i },
  }),
};

export const HomePage = () => {
  const {
    user,
    favorites,
    notifications,
    addFavorite,
    removeFavorite,
    markAllNotificationsRead,
  } = useContext(AuthContext);
  const { markNotificationRead, handleDelete, handleToggleImportant } = useNotificationActions();
  const [openFavoriteAppId, setOpenFavoriteAppId] = useState<string | null>(null);
  const [openRecentAppId, setOpenRecentAppId] = useState<string | null>(null);
  const navigate = useNavigate();

  const unreadCount = notifications.filter((n) => !n.read).length;

  const routesByApp = useRoutesByApp();
  const appsById = useAppsById();

  const launchableFavorites = useMemo(
    () => favorites.filter((fav) => isLaunchableApp(appsById[fav.id])),
    [favorites, appsById],
  );

  const recentApps = useMemo(() => {
    const ids = getRecentAppIds();
    return ids
      .map((id) => appsById[id])
      .filter(isLaunchableApp);
  }, [appsById]);

  const togglePin = async (appId: string) => {
    const app = appsById[appId];
    if (!isLaunchableApp(app)) return;

    const isPinned = favorites.some((f) => f.id === appId);
    if (isPinned) {
      await removeFavorite(appId);
    } else {
      await addFavorite(appId);
    }
  };

  const topNotifications = notifications.slice(0, 4);

  return (
    <div id="home-page" className="home-wrap" data-tour="home-page">
      {/* HEADER */}
      <motion.div
        className="home-header"
        initial="hidden"
        animate="show"
        variants={fadeUp}
      >
        <div className="home-header-left">
          <h1 className="home-title">
            {greeting()}, <span className="home-name">{user?.name}</span>
          </h1>
          <p className="home-subtitle">Bem-vindo à Minha DELPI.</p>
        </div>

        <div className="home-header-right">
          <span className="home-pill">
            <span className="status-dot" />
            Online
          </span>

          {user?.is_superadmin && (
            <button
              className="home-ghost"
              onClick={() => navigate("/admin")}
              type="button"
              title="Acessar Admin"
            >
              <Shield size={18} />
              <span>Admin</span>
              <ArrowRight size={16} />
            </button>
          )}
        </div>
      </motion.div>

      {/* QUICK SUMMARY */}
      <motion.div
        className="home-summary"
        initial="hidden"
        animate="show"
        variants={fadeUp}
        custom={1}
      >
        <PortalTourHomeEntry />

        <SummaryCard
          icon={<Bell size={18} />}
          title="Notificações"
          value={unreadCount}
          subtitle={unreadCount === 1 ? "não lida" : "não lidas"}
          onClick={() => navigate("/notifications")}
          dataTour="home-summary-notifications"
        />

        <SummaryCard
          icon={<Star size={18} />}
          title="Favoritos"
          value={launchableFavorites.length}
          subtitle="aplicações fixadas"
          onClick={() => {
            const el = document.querySelector("#home-favorites");
            el?.scrollIntoView({ behavior: "smooth", block: "start" });
          }}
        />

        <SummaryCard
          icon={<Activity size={18} />}
          title="Continuar"
          value={recentApps.length}
          subtitle="recentes"
          onClick={() => {
            const el = document.querySelector("#home-recent");
            el?.scrollIntoView({ behavior: "smooth", block: "start" });
          }}
        />
      </motion.div>

      {/* MAIN GRID */}
      <div className="home-grid-main">
        {/* FAVORITES */}
        <motion.section
          id="home-favorites"
          className="home-panel"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={2}
        >
          <PanelHeader title="Favoritos" hint="Acesso rápido às aplicações mais usadas" />

          {launchableFavorites.length === 0 ? (
            <EmptyState text="Você ainda não fixou aplicações. Use o botão Apps na sidebar." />
          ) : (
          <div className="launcher-pinned-grid">
            {launchableFavorites.map((favorite) => {
              const app = appsById[favorite.id] ?? favorite;
              const appRoutes = routesByApp[favorite.id] ?? [];

              return (
                <AppLauncherCard
                  variant="home"
                  key={favorite.id}
                  app={app}
                  routes={appRoutes}
                  isOpen={openFavoriteAppId === favorite.id}
                  isPinned={true}
                  onToggleOpen={(id) => {
                    setOpenRecentAppId(null);
                    setOpenFavoriteAppId((prev) => (prev === id ? null : id));
                  }}
                  onOpenSingle={(id) => {
                    const route = routesByApp[id]?.[0];
                    const catalogApp = appsById[id];
                    if (route) {
                      navigate(route.path);
                      return;
                    }
                    if (catalogApp?.basePath) navigate(catalogApp.basePath);
                  }}
                  onGoToRoute={(path) => navigate(path)}
                  onTogglePin={togglePin}
                />
              );
            })}
          </div>
          )}
        </motion.section>

        {/* RECENT */}
        <motion.section
          id="home-recent"
          className="home-panel"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={3}
        >
          <PanelHeader title="Continuar trabalhando" hint="Últimas aplicações acessadas" />

          {recentApps.length === 0 ? (
            <EmptyState text="Nada por aqui ainda. Abra um app e ele aparecerá aqui." />
          ) : (
          <div className="launcher-pinned-grid">
            {recentApps.map((app) => {
              if (!app) return null;

              const appRoutes = routesByApp[app.id] ?? [];

              return (
                <AppLauncherCard
                  variant="home"
                  key={app.id}
                  app={app}
                  routes={appRoutes}
                  isOpen={openRecentAppId === app.id}
                  isPinned={favorites.some((f) => f.id === app.id)}
                  onToggleOpen={(id) => {
                    setOpenFavoriteAppId(null);
                    setOpenRecentAppId((prev) => (prev === id ? null : id));
                  }}
                  onOpenSingle={(id) => {
                    const route = routesByApp[id]?.[0];
                    const catalogApp = appsById[id];
                    if (route) {
                      navigate(route.path);
                      return;
                    }
                    if (catalogApp?.basePath) navigate(catalogApp.basePath);
                  }}
                  onGoToRoute={(path) => navigate(path)}
                  onTogglePin={togglePin}
                />
              );
            })}
          </div>
          )}
        </motion.section>

        {/* NOTIFICATIONS */}
        <motion.section
          id="home-notifications"
          className="home-panel home-panel-wide"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={4}
        >
          <PanelHeader
            title="Notificações recentes"
            hint="Acompanhe atualizações e ações pendentes"
            actionLabel="Ver todas"
            onAction={() => navigate("/notifications")}
          />

          {notifications.length === 0 ? (
            <EmptyState text="Nenhuma notificação recente." />
          ) : (
            <>
              {unreadCount > 0 ? (
                <button
                  type="button"
                  className="home-notif-mark-all"
                  onClick={() => void markAllNotificationsRead()}
                >
                  Marcar todas como lidas
                </button>
              ) : null}

              <div className="home-notif-list">
                {topNotifications.map((n) => (
                  <NotificationCard
                    key={n.id}
                    notification={n}
                    compact
                    onMarkRead={markNotificationRead}
                    onDelete={(id) => void handleDelete(id)}
                    onToggleImportant={(id, isImportant) =>
                      void handleToggleImportant(id, isImportant)
                    }
                  />
                ))}
              </div>
            </>
          )}
        </motion.section>

        {/* ADMIN ONLY */}
        {user?.is_superadmin && (
          <motion.section
            className="home-panel"
            initial="hidden"
            animate="show"
            variants={fadeUp}
            custom={5}
          >
            <PanelHeader title="Painel administrativo" hint="Atalhos para gestão" />

            <div className="home-admin-actions">
              <motion.button
                className="home-action"
                type="button"
                onClick={() => navigate("/admin")}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
              >
                <Shield size={18} />
                <span>Gerenciar Admin</span>
                <ArrowRight size={16} />
              </motion.button>

              <div className="home-admin-hint">
                Dica: aqui depois podemos mostrar “mudanças recentes”, “apps
                aguardando publicação”, “erros de integração”, etc.
              </div>
            </div>
          </motion.section>
        )}
      </div>
    </div>
  );
};

function PanelHeader({
  title,
  hint,
  actionLabel,
  onAction,
}: {
  title: string;
  hint?: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="home-panel-header">
      <div>
        <h3 className="home-panel-title">{title}</h3>
        {hint ? <p className="home-panel-hint">{hint}</p> : null}
      </div>
      {actionLabel && onAction ? (
        <button type="button" className="home-panel-action" onClick={onAction}>
          {actionLabel}
          <ArrowRight size={14} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="home-empty">{text}</div>;
}

function SummaryCard({
  icon,
  title,
  value,
  subtitle,
  onClick,
  dataTour,
}: {
  icon: React.ReactNode;
  title: string;
  value: number | string;
  subtitle: string;
  onClick?: () => void;
  dataTour?: string;
}) {
  return (
    <motion.button
      type="button"
      className="home-summary-card"
      data-tour={dataTour}
      onClick={onClick}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <span className="home-summary-icon">{icon}</span>

      <span className="home-summary-main">
        <span className="home-summary-title">{title}</span>
        <span className="home-summary-value">{value}</span>
        <span className="home-summary-sub">{subtitle}</span>
      </span>
      <span className="home-summary-arrow">
        <ArrowRight size={16} />
      </span>
    </motion.button>
  );
}