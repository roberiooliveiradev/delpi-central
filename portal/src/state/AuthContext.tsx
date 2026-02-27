// src/state/AuthContext.tsx

import React, {
  createContext,
  useEffect,
  useState,
  useRef,
  useCallback,
} from "react";
import keycloak from "../data/keycloakClient";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import { useSocket } from "../hooks/useSocket";

import type {
  MeResponse,
  AppItem,
  RouteItem,
  DashboardResponse,
  NotificationItem,
  FavoriteAppItem,
} from "../data/coreApi";

interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  token?: string;
  user?: MeResponse;
  apps: AppItem[];
  routes: RouteItem[];
  dashboard?: DashboardResponse;
  favorites?: FavoriteAppItem[];
  notifications: NotificationItem[];
  markNotificationRead: (id: string) => Promise<void>;
  markAllNotificationsRead: () => Promise<void>;
  login: () => void;
  logout: () => void;
  reload: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  loading: true,
  apps: [],
  routes: [],
  favorites: [],
  notifications: [],
  markNotificationRead: async () => {},
  markAllNotificationsRead: async () => {},
  login: () => {},
  logout: () => {},
  reload: async () => {},
  refreshToken: async () => {},
});

type AdminChangedEvent = {
  entity?: "apps" | "routes" | "rbac" | "plugins" | "dashboard" | string;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | undefined>();
  const [user, setUser] = useState<MeResponse | undefined>();
  const [apps, setApps] = useState<AppItem[]>([]);
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [dashboard, setDashboard] =
    useState<DashboardResponse | undefined>();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [favorites, setFavorites] = useState<FavoriteAppItem[]>([]);

  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
    null
  );

  const syncQueueRef = useRef<Set<string>>(new Set());
  const syncTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isSyncingRef = useRef(false);
  const pendingResyncRef = useRef(false);
  const initializedRef = useRef(false);

  const buildCoreApi = useCallback(() => {
    const apiClient = new ApiClient("", () => keycloak.token);
    return new CoreApi(apiClient);
  }, []);

  // =====================================================
  // CORE LOAD
  // =====================================================

  const loadCoreData = useCallback(async () => {
    if (!keycloak.token) return;
    const coreApi = buildCoreApi();

    const [
      me,
      appsResponse,
      routesResponse,
      dashboardData,
      notificationsData,
      appsFav,
    ] = await Promise.all([
      coreApi.getMe(),
      coreApi.getApps(),
      coreApi.getRoutes(),
      coreApi.getDashboard(),
      coreApi.getNotifications(),
      coreApi.getFavoriteApps(),
    ]);

    setUser(me);
    setApps(appsResponse);
    setRoutes(routesResponse);
    setDashboard(dashboardData);
    setNotifications(notificationsData);
    setFavorites(appsFav);
  }, [buildCoreApi]);

  // =====================================================
  // ENTERPRISE SYNC ENGINE
  // =====================================================

  const runSyncBatch = useCallback(
    async (entities: string[]) => {
      if (!keycloak.token) return;
      const coreApi = buildCoreApi();
      const tasks: Promise<any>[] = [];

      const needsApps =
        entities.includes("apps") ||
        entities.includes("plugins") ||
        entities.includes("rbac");

      const needsRoutes =
        entities.includes("routes") ||
        entities.includes("apps") ||
        entities.includes("plugins") ||
        entities.includes("rbac");

      const needsMe = entities.includes("rbac");
      const needsDashboard = entities.includes("dashboard");

      if (needsApps)
        tasks.push(coreApi.getApps().then(setApps));

      if (needsRoutes)
        tasks.push(coreApi.getRoutes().then(setRoutes));

      if (needsMe)
        tasks.push(coreApi.getMe().then(setUser));

      if (needsDashboard)
        tasks.push(coreApi.getDashboard().then(setDashboard));

      await Promise.all(tasks);
    },
    [buildCoreApi]
  );

  const scheduleSync = useCallback(
    (entity: string) => {
      const normalized = [
        "apps",
        "routes",
        "rbac",
        "plugins",
        "dashboard",
      ].includes(entity)
        ? entity
        : "apps";

      syncQueueRef.current.add(normalized);

      if (syncTimeoutRef.current) return;

      syncTimeoutRef.current = setTimeout(async () => {
        syncTimeoutRef.current = null;

        if (isSyncingRef.current) {
          pendingResyncRef.current = true;
          return;
        }

        isSyncingRef.current = true;

        try {
          const entities = Array.from(syncQueueRef.current);
          syncQueueRef.current.clear();
          await runSyncBatch(entities);
        } finally {
          isSyncingRef.current = false;

          if (
            pendingResyncRef.current ||
            syncQueueRef.current.size > 0
          ) {
            pendingResyncRef.current = false;
            const entities = Array.from(syncQueueRef.current);
            syncQueueRef.current.clear();
            if (entities.length > 0) {
              isSyncingRef.current = true;
              await runSyncBatch(entities);
              isSyncingRef.current = false;
            }
          }
        }
      }, 120);
    },
    [runSyncBatch]
  );

  // =====================================================
  // SOCKET
  // =====================================================
  useSocket({
     token: !loading && isAuthenticated && token ? token : undefined,
    onConnected: async () => {
      await loadCoreData();
    },
    onNotification: (data) => {
      setNotifications((prev) => [data, ...prev]);
    },
    onAdminChanged: (event: AdminChangedEvent) => {
      if (event?.entity) scheduleSync(event.entity);
    },
  });

  // =====================================================
  // TOKEN REFRESH
  // =====================================================

  const refreshToken = useCallback(async () => {
    try {
      const refreshed = await keycloak.updateToken(60);
      if (refreshed && keycloak.token && keycloak.token !== token) {
        setToken(keycloak.token);
      }
    } catch {
      keycloak.logout();
    }
  }, []);

  const startTokenRefresh = () => {
    refreshIntervalRef.current = setInterval(
      refreshToken,
      60000
    );
  };

  // =====================================================
  // INIT
  // =====================================================

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    keycloak
      .init({
        onLoad: "login-required",
        pkceMethod: "S256",
        checkLoginIframe: false,
      })
      .then(async (authenticated) => {
        setIsAuthenticated(authenticated);
        setToken(keycloak.token);

        if (authenticated) {
          await loadCoreData();
        }

        startTokenRefresh();
      })
      .finally(() => setLoading(false));

    return () => {
      if (refreshIntervalRef.current)
        clearInterval(refreshIntervalRef.current);
      if (syncTimeoutRef.current)
        clearTimeout(syncTimeoutRef.current);
    };
  }, [loadCoreData, refreshToken]);

  const login = () => keycloak.login();
  const logout = () => keycloak.logout();

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        loading,
        token,
        user,
        apps,
        routes,
        dashboard,
        favorites,
        notifications,
        markNotificationRead: async () => {},
        markAllNotificationsRead: async () => {},
        login,
        logout,
        reload: loadCoreData,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};