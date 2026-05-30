// src/ui/MyProfile.tsx

import { useContext, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import { AuthContext } from "../state/AuthContext";
import { useRoutesByApp } from "../hooks/useRoutesByApp";
import { useAppsById } from "../hooks/useAppsById";
import { filterLaunchableApps, isLaunchableApp } from "../utils/launchableApps";

import { AppLauncherCard } from "../components/AppLauncherCard";
import { DataTable } from "../components/DataTable";
import type {
  DataTableColumn,
  DataTableSort,
} from "../components/DataTable";

import {
  Grid,
  Star,
  Users,
  Shield,
  ArrowRight,
} from "lucide-react";

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

const fadeUp = {
  hidden: { opacity: 0, y: 10 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.22, delay: 0.04 * i },
  }),
};

/* =========================================
   COMPONENT
========================================= */

export const MyProfile = () => {
  const { user, apps, favorites, addFavorite, removeFavorite } =
    useContext(AuthContext);

  const navigate = useNavigate();
  const routesByApp = useRoutesByApp();
  const appsById = useAppsById();

  const [query, setQuery] = useState("");

  const [roleSort, setRoleSort] = useState<DataTableSort>({
    sort: "name",
    direction: "asc",
  });

  const [groupSort, setGroupSort] = useState<DataTableSort>({
    sort: "name",
    direction: "asc",
  });

  const [permissionSort, setPermissionSort] = useState<DataTableSort>({
    sort: "name",
    direction: "asc",
  });

  const [rolePage, setRolePage] = useState(1);
  const [groupPage, setGroupPage] = useState(1);
  const [permissionPage, setPermissionPage] = useState(1);

  const [rolePageSize, setRolePageSize] = useState(5);
  const [groupPageSize, setGroupPageSize] = useState(5);
  const [permissionPageSize, setPermissionPageSize] = useState(5);

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

  function sortRows<T extends Record<string, any>>(
    rows: T[],
    sort?: DataTableSort
  ) {
    if (!sort?.sort) return rows;

    const dir = sort.direction === "desc" ? -1 : 1;
    const key = sort.sort;

    return [...rows].sort((a, b) => {
      const av = a[key];
      const bv = b[key];

      if (av == null) return -1 * dir;
      if (bv == null) return 1 * dir;

      return String(av).localeCompare(String(bv)) * dir;
    });
  }

  function paginateRows<T>(rows: T[], page: number, pageSize: number) {
    const start = (page - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }

  const sortedRoleRows = useMemo(
    () => sortRows(roleRows, roleSort),
    [roleRows, roleSort]
  );

  const sortedGroupRows = useMemo(
    () => sortRows(groupRows, groupSort),
    [groupRows, groupSort]
  );

  const sortedPermissionRows = useMemo(
    () => sortRows(permissionRows, permissionSort),
    [permissionRows, permissionSort]
  );

  const paginatedRoleRows = useMemo(
    () => paginateRows(sortedRoleRows, rolePage, rolePageSize),
    [sortedRoleRows, rolePage, rolePageSize]
  );

  const paginatedGroupRows = useMemo(
    () => paginateRows(sortedGroupRows, groupPage, groupPageSize),
    [sortedGroupRows, groupPage, groupPageSize]
  );

  const paginatedPermissionRows = useMemo(
    () => paginateRows(sortedPermissionRows, permissionPage, permissionPageSize),
    [sortedPermissionRows, permissionPage, permissionPageSize]
  );

  /* =========================================
     TABLE COLUMNS
  ========================================= */

  const roleColumns: DataTableColumn<RoleRow>[] = [
    {
      key: "name",
      header: "Papel",
      sortable: true,
    },
  ];

  const groupColumns: DataTableColumn<GroupRow>[] = [
    {
      key: "name",
      header: "Grupo",
      sortable: true,
    },
  ];

  const permissionColumns: DataTableColumn<PermissionRow>[] = [
    {
      key: "name",
      header: "Permissão",
      sortable: true,
    },
  ];

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

  const rolePagination = {
    page: rolePage,
    pageSize: rolePageSize,
    total: sortedRoleRows.length,
    totalPages: Math.max(1, Math.ceil(sortedRoleRows.length / rolePageSize)),
  };

  const groupPagination = {
    page: groupPage,
    pageSize: groupPageSize,
    total: sortedGroupRows.length,
    totalPages: Math.max(1, Math.ceil(sortedGroupRows.length / groupPageSize)),
  };

  const permissionPagination = {
    page: permissionPage,
    pageSize: permissionPageSize,
    total: sortedPermissionRows.length,
    totalPages: Math.max(
      1,
      Math.ceil(sortedPermissionRows.length / permissionPageSize)
    ),
  };


  /* =========================================
     RENDER
  ========================================= */

  return (
    <div className="home-wrap">

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
        initial="hidden"
        animate="show"
        variants={fadeUp}
        custom={1}
      >

        {summary.apps > 0 && (
          <SummaryCard
            icon={<Grid size={18} />}
            title="Aplicações"
            value={summary.apps}
            subtitle="disponíveis"
            onClick={() => scrollTo("profile-apps")}
          />
        )}

        {summary.favorites > 0 && (
          <SummaryCard
            icon={<Star size={18} />}
            title="Favoritos"
            value={summary.favorites}
            subtitle="aplicações fixadas"
            onClick={() => scrollTo("profile-apps")}
          />
        )}

        {summary.groups > 0 && (
          <SummaryCard
            icon={<Users size={18} />}
            title="Grupos"
            value={summary.groups}
            subtitle="vinculados"
            onClick={() => scrollTo("profile-groups")}
          />
        )}

        {summary.roles > 0 && (
          <SummaryCard
            icon={<Shield size={18} />}
            title="Papéis"
            value={summary.roles}
            subtitle="vinculados"
            onClick={() => scrollTo("profile-roles")}
          />
        )}

        {summary.permissions > 0 && (
          <SummaryCard
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
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={2}
        >
          <PanelHeader
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
          </div>
        </motion.section>

        {/* GROUPS */}

        {groupRows.length > 0 && (
          <motion.section
            id="profile-groups"
            className="home-panel"
            initial="hidden"
            animate="show"
            variants={fadeUp}
            custom={3}
          >
            <PanelHeader
              title="Grupos"
              hint="Grupos aos quais você pertence"
            />

            <DataTable<GroupRow>
              columns={groupColumns}
              data={paginatedGroupRows}
              pagination={groupPagination}
              onPageChange={setGroupPage}
              onPageSizeChange={setGroupPageSize}
              sort={groupSort}
              onSortChange={setGroupSort}
              emptyText="Nenhum grupo atribuído."
            />
          </motion.section>
        )}

        {/* ROLES */}

        {roleRows.length > 0 && (
          <motion.section
            id="profile-roles"
            className="home-panel"
            initial="hidden"
            animate="show"
            variants={fadeUp}
            custom={4}
          >
            <PanelHeader
              title="Papéis"
              hint="Papéis atribuídos ao usuário"
            />

            <DataTable<RoleRow>
              columns={roleColumns}
              data={paginatedRoleRows}
              pagination={rolePagination}
              onPageChange={setRolePage}
              onPageSizeChange={setRolePageSize}
              sort={roleSort}
              onSortChange={setRoleSort}
              emptyText="Nenhum papel atribuído."
            />
          </motion.section>
        )}

        {/* PERMISSIONS */}

        {permissionRows.length > 0 && (
          <motion.section
            id="profile-permissions"
            className="home-panel"
            initial="hidden"
            animate="show"
            variants={fadeUp}
            custom={5}
          >
            <PanelHeader
              title="Permissões"
              hint="Permissões efetivas do usuário"
            />

            <DataTable<PermissionRow>
              columns={permissionColumns}
              data={paginatedPermissionRows}
              pagination={permissionPagination}
              onPageChange={setPermissionPage}
              onPageSizeChange={setPermissionPageSize}
              sort={permissionSort}
              onSortChange={setPermissionSort}
              emptyText="Nenhuma permissão atribuída."
            />
          </motion.section>
        )}


        {/* APPS */}

        <motion.section
          id="profile-apps"
          className="home-panel home-panel-wide"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={6}
        >
          <PanelHeader
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

/* =========================================
   HELPERS
========================================= */

function PanelHeader({
  title,
  hint,
}: {
  title: string;
  hint?: string;
}) {
  return (
    <div className="home-panel-header">
      <div>
        <h3 className="home-panel-title">{title}</h3>
        {hint && <p className="home-panel-hint">{hint}</p>}
      </div>
    </div>
  );
}

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

function SummaryCard({
  icon,
  title,
  value,
  subtitle,
  onClick,
}: {
  icon: React.ReactNode;
  title: string;
  value: number | string;
  subtitle: string;
  onClick?: () => void;
}) {
  return (
    <motion.button
      type="button"
      className="home-summary-card"
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