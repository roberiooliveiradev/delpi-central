// src/ui/MyProfile.tsx

import { useContext, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import { useRoutesByApp } from "../hooks/useRoutesByApp";
import { useAppsById } from "../hooks/useAppsById";
import { filterLaunchableApps, isLaunchableApp } from "../utils/launchableApps";

import { AppLauncherCard } from "../components/AppLauncherCard";
import { useConfirmDialog } from "../components/ConfirmDialogProvider";
import { startPortalTour } from "../tour/PortalTour";
import { restartPortalTourRemote } from "../tour/portalTourPersistence";
import { resumePortalTour } from "../tour/portalTourSession";
import { PortalTourAchievementsPanel } from "../tour/PortalTourAchievementsPanel";
import { ProfileRbacCardGrid } from "./profile/ProfileRbacCardGrid";

import {
  Grid,
  Star,
  Users,
  Shield,
  Compass,
  RotateCcw,
  KeyRound,
} from "lucide-react";

import {
  homeFadeUp,
  HomePanelHeader,
  HomeSummaryCard,
} from "./home/HomePagePrimitives";

import "./MyProfile.css";

/* =========================================
   TYPES
========================================= */

type RoleRow = {
  name: string;
};

type GroupRow = {
  name: string;
};

type RouteItem = {
  app: string;
  path: string;
  label?: string | null;
  icon?: string | null;
};

type PermissionRow = {
  name: string;
};

type SearchResult =
  | { kind: "app"; app: any; score: number }
  | { kind: "route"; app: any; route: RouteItem; score: number };

/* =========================================
   ANIMATION
========================================= */

const fadeUp = homeFadeUp;

/* =========================================
   COMPONENT
========================================= */

export const MyProfile = () => {
  const {
    user,
    apps,
    favorites,
    addFavorite,
    removeFavorite,
    getAccessToken,
    refreshToken,
  } = useContext(AuthContext);

  const navigate = useNavigate();
  const confirm = useConfirmDialog();
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
  const routesByApp = useRoutesByApp();
  const appsById = useAppsById();

  const [query, setQuery] = useState("");

  const [permissionPage, setPermissionPage] = useState(1);
  const [permissionPageSize, setPermissionPageSize] = useState(12);

  /* =========================================
     FAVORITES
  ========================================= */

  const togglePin = async (appId: string) => {
    if (!isLaunchableApp(appsById[appId])) return;

    const isPinned = favorites.some((f) => f.id === appId);

    if (isPinned) {
      await removeFavorite(appId);
    } else {
      await addFavorite(appId);
    }
  };

  const sortedApps = useMemo(() => {
    const launchableApps = filterLaunchableApps(apps);
    const favIds = favorites.map((f) => f.id);

    const pinned = launchableApps.filter((a) => favIds.includes(a.id));
    const rest = launchableApps.filter((a) => !favIds.includes(a.id));

    return [...pinned, ...rest];
  }, [apps, favorites]);

  /* =========================================
     SEARCH
  ========================================= */

  const searchResults: SearchResult[] = useMemo(() => {
    const q = normalize(query);
    if (!q) return [];

    const results: SearchResult[] = [];

    for (const app of filterLaunchableApps(apps)) {
      const appName = normalize(app.name);

      const appScore =
        appName === q
          ? 100
          : appName.startsWith(q)
          ? 70
          : appName.includes(q)
          ? 50
          : 0;

      if (appScore > 0) {
        results.push({ kind: "app", app, score: appScore });
      }

      const appRoutes = routesByApp[app.id] ?? [];

      for (const route of appRoutes) {
        const label = normalize(route.label ?? route.path);
        const path = normalize(route.path);

        const score =
          label === q || path === q
            ? 95
            : label.startsWith(q) || path.startsWith(q)
            ? 65
            : label.includes(q) || path.includes(q)
            ? 45
            : 0;

        if (score > 0) {
          results.push({
            kind: "route",
            app,
            route,
            score,
          });
        }
      }
    }

    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, 24);
  }, [apps, query, routesByApp]);

  const isSearching = normalize(query).length > 0;

  /* =========================================
     SCROLL NAVIGATION
  ========================================= */

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    el?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  /* =========================================
     DATA PREP
  ========================================= */

  const roleRows: RoleRow[] = useMemo(
    () => user?.roles?.map((r) => ({ name: r })) ?? [],
    [user]
  );

  const groupRows: GroupRow[] = useMemo(
    () => user?.groups?.map((g) => ({ name: g })) ?? [],
    [user]
  );

  const permissionRows: PermissionRow[] = useMemo(
    () => user?.permissions?.map((p) => ({ name: p })) ?? [],
    [user]
  );

  /* =========================================
     SORTING
  ========================================= */

  function sortByName<T extends { name: string }>(rows: T[]): T[] {
    return [...rows].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  }

  function paginateRows<T>(rows: T[], page: number, pageSize: number) {
    const start = (page - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }

  const sortedGroupRows = useMemo(() => sortByName(groupRows), [groupRows]);
  const sortedRoleRows = useMemo(() => sortByName(roleRows), [roleRows]);
  const sortedPermissionRows = useMemo(
    () => sortByName(permissionRows),
    [permissionRows],
  );

  const paginatedPermissionRows = useMemo(
    () => paginateRows(sortedPermissionRows, permissionPage, permissionPageSize),
    [sortedPermissionRows, permissionPage, permissionPageSize],
  );

  const groupCardItems = useMemo(
    () =>
      sortedGroupRows.map((row) => ({
        id: row.name,
        label: row.name,
      })),
    [sortedGroupRows],
  );

  const roleCardItems = useMemo(
    () =>
      sortedRoleRows.map((row) => ({
        id: row.name,
        label: row.name,
      })),
    [sortedRoleRows],
  );

  const permissionCardItems = useMemo(
    () =>
      paginatedPermissionRows.map((row) => ({
        id: row.name,
        label: row.name,
      })),
    [paginatedPermissionRows],
  );

  /* =========================================
     SUMMARY
  ========================================= */

  const summary = {
    apps: apps.length,
    favorites: favorites.length,
    roles: user?.roles?.length ?? 0,
    groups: user?.groups?.length ?? 0,
    permissions: user?.permissions?.length ?? 0,
  };

  function normalize(s: string) {
    return (s ?? "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "")
      .trim();
  }

  const handleContinueTour = () => {
    resumePortalTour();
    navigate("/");
  };

  const handleResetTour = async () => {
    if (!user?.id) return;

    const confirmed = await confirm({
      title: "Zerar progresso do tour?",
      message:
        "Isso apaga conquistas, XP e ranking desta versão do tour. A ação não pode ser desfeita.",
      confirmText: "Zerar e recomeçar",
      cancelText: "Cancelar",
      danger: true,
    });

    if (!confirmed) return;

    await restartPortalTourRemote(coreApi, user.id);
    startPortalTour();
    navigate("/");
  };


  const permissionPaginationTotal = sortedPermissionRows.length;


  /* =========================================
     RENDER
  ========================================= */

  return (
    <div className="home-wrap profile-page" data-tour="profile-page">

      {/* HEADER */}

      <motion.div
        className="home-header"
        initial="hidden"
        animate="show"
        variants={fadeUp}
      >
        <div className="home-header-left">
          <h1 className="home-title">
            Perfil de <span className="home-name">{user?.name}</span>
          </h1>

          <p className="home-subtitle">
            Informações da sua conta e acessos na Minha DELPI.
          </p>
        </div>

        <div className="home-header-right">
          <span className="home-pill">
            <span className="status-dot" />
            Conta ativa
          </span>
        </div>
      </motion.div>

      {/* SUMMARY */}

      <motion.div
        className="home-summary"
        data-tour="profile-rbac-summary"
        initial="hidden"
        animate="show"
        variants={fadeUp}
        custom={1}
      >

        {summary.apps > 0 && (
          <HomeSummaryCard
            icon={<Grid size={18} />}
            title="Aplicações"
            value={summary.apps}
            subtitle="disponíveis"
            onClick={() => scrollTo("profile-apps")}
          />
        )}

        {summary.favorites > 0 && (
          <HomeSummaryCard
            icon={<Star size={18} />}
            title="Favoritos"
            value={summary.favorites}
            subtitle="aplicações fixadas"
            onClick={() => scrollTo("profile-apps")}
          />
        )}

        {summary.groups > 0 && (
          <HomeSummaryCard
            icon={<Users size={18} />}
            title="Grupos"
            value={summary.groups}
            subtitle="vinculados"
            onClick={() => scrollTo("profile-groups")}
          />
        )}

        {summary.roles > 0 && (
          <HomeSummaryCard
            icon={<Shield size={18} />}
            title="Papéis"
            value={summary.roles}
            subtitle="vinculados"
            onClick={() => scrollTo("profile-roles")}
          />
        )}

        {summary.permissions > 0 && (
          <HomeSummaryCard
            icon={<Shield size={18} />}
            title="Permissões"
            value={summary.permissions}
            subtitle="ativas"
            onClick={() => scrollTo("profile-permissions")}
          />
        )}

      </motion.div>

      {/* MAIN GRID */}

      <div className="home-grid-main">

        {/* USER INFO */}

        <motion.section
          id="profile-info"
          className="home-panel"
          data-tour="profile-info"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={2}
        >
          <HomePanelHeader
            title="Informações da conta"
            hint="Dados básicos do usuário"
          />

          <div className="profile-info">
            <ProfileItem label="Nome" value={user?.name} />
            <ProfileItem label="Email" value={user?.email} />
            <ProfileItem label="ID" value={user?.id} />
            <ProfileItem
              label="Superadmin"
              value={user?.is_superadmin ? "Sim" : "Não"}
            />
            <div className="profile-tour-actions">
              <button
                type="button"
                className="home-panel-action profile-tour-resume"
                data-tour="profile-tour-resume"
                onClick={handleContinueTour}
              >
                <Compass size={14} aria-hidden="true" />
                Continuar explorando
              </button>
              <button
                type="button"
                className="profile-tour-reset"
                data-tour="profile-tour-reset"
                onClick={() => void handleResetTour()}
              >
                <RotateCcw size={14} aria-hidden="true" />
                Zerar progresso e recomeçar
              </button>
            </div>
          </div>
        </motion.section>

        <motion.div
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={2.5}
        >
          <PortalTourAchievementsPanel />
        </motion.div>

        {(groupRows.length > 0 ||
          roleRows.length > 0 ||
          permissionRows.length > 0) && (
          <div className="profile-rbac-grid">
            {groupRows.length > 0 && (
              <motion.section
                id="profile-groups"
                className="home-panel profile-rbac-panel"
                data-tour="profile-groups"
                initial="hidden"
                animate="show"
                variants={fadeUp}
                custom={3}
              >
                <HomePanelHeader
                  title="Grupos"
                  hint="Grupos aos quais você pertence"
                  badge={
                    <span className="profile-rbac-badge">{groupRows.length}</span>
                  }
                />

                <ProfileRbacCardGrid
                  items={groupCardItems}
                  icon={<Users size={18} />}
                  emptyText="Nenhum grupo atribuído."
                  ariaLabel="Grupos do usuário"
                />
              </motion.section>
            )}

            {roleRows.length > 0 && (
              <motion.section
                id="profile-roles"
                className="home-panel profile-rbac-panel"
                data-tour="profile-roles"
                initial="hidden"
                animate="show"
                variants={fadeUp}
                custom={4}
              >
                <HomePanelHeader
                  title="Papéis"
                  hint="Papéis atribuídos ao usuário"
                  badge={
                    <span className="profile-rbac-badge">{roleRows.length}</span>
                  }
                />

                <ProfileRbacCardGrid
                  items={roleCardItems}
                  icon={<Shield size={18} />}
                  emptyText="Nenhum papel atribuído."
                  ariaLabel="Papéis do usuário"
                />
              </motion.section>
            )}

            {permissionRows.length > 0 && (
              <motion.section
                id="profile-permissions"
                className="home-panel profile-rbac-panel profile-rbac-panel--full"
                data-tour="profile-permissions"
                initial="hidden"
                animate="show"
                variants={fadeUp}
                custom={5}
              >
                <HomePanelHeader
                  title="Permissões"
                  hint="Permissões efetivas do usuário"
                  badge={
                    <span className="profile-rbac-badge">{permissionRows.length}</span>
                  }
                />

                <ProfileRbacCardGrid
                  items={permissionCardItems}
                  icon={<KeyRound size={18} />}
                  variant="permission"
                  emptyText="Nenhuma permissão atribuída."
                  ariaLabel="Permissões do usuário"
                  page={permissionPage}
                  pageSize={permissionPageSize}
                  total={permissionPaginationTotal}
                  pageSizeOptions={[12, 24, 48]}
                  onPageChange={setPermissionPage}
                  onPageSizeChange={(size) => {
                    setPermissionPageSize(size);
                    setPermissionPage(1);
                  }}
                />
              </motion.section>
            )}
          </div>
        )}

        {/* APPS */}

        <motion.section
          id="profile-apps"
          className="home-panel home-panel-wide"
          data-tour="profile-apps"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={6}
        >
          <HomePanelHeader
            title="Aplicações disponíveis"
            hint="Aplicações às quais você tem acesso"
          />

          <div className="apps-search">
            <Search size={16} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Pesquisar aplicativos..."
            />
          </div>

          <div className="launcher-pinned-grid">

            {!isSearching &&
              sortedApps.map((app) => {
                const appRoutes = routesByApp[app.id] ?? [];

                return (
                  <AppLauncherCard
                    key={app.id}
                    variant="launcher"
                    app={app}
                    routes={appRoutes}
                    isPinned={favorites.some((f) => f.id === app.id)}
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

            {isSearching && (
              <>
                {searchResults.length === 0 && (
                  <div className="apps-empty">
                    Nenhum resultado encontrado.
                  </div>
                )}

                {searchResults.map((r, idx) => {

                  if (r.kind === "app") {
                    const appRoutes = routesByApp[r.app.id] ?? [];

                    return (
                      <AppLauncherCard
                        key={`app:${r.app.id}:${idx}`}
                        variant="launcher"
                        app={r.app}
                        routes={appRoutes}
                        isPinned={favorites.some(
                          (f) => f.id === r.app.id
                        )}
                        searchKind="app"
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
                  }

                  const isPinned = favorites.some(
                    (f) => f.id === r.app.id
                  );

                  return (
                    <AppLauncherCard
                      key={`route:${r.route.path}:${idx}`}
                      variant="launcher"
                      app={r.app}
                      routes={[r.route]}
                      isPinned={isPinned}
                      searchKind="route"
                      onOpenSingle={() => navigate(r.route.path)}
                      onGoToRoute={(path) => navigate(path)}
                      onTogglePin={togglePin}
                    />
                  );
                })}
              </>
            )}

          </div>
        </motion.section>
      </div>
    </div>
  );
};

function ProfileItem({
  label,
  value,
}: {
  label: string;
  value?: string;
}) {
  return (
    <div className="profile-item">
      <span className="profile-label">{label}</span>
      <span className="profile-value">{value ?? "-"}</span>
    </div>
  );
}