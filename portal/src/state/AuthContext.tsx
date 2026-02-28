import React, {
  createContext,
  useEffect,
  useState,
  useRef,
  useCallback,
} from "react";
import keycloak, { initKeycloak } from "../data/keycloakClient";
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
  initialized: boolean;
  token?: string;
  user?: MeResponse;
  apps: AppItem[];
  routes: RouteItem[];
  dashboard?: DashboardResponse;
  favorites: FavoriteAppItem[];
  notifications: NotificationItem[];

  addFavorite: (appId: string) => Promise<void>;
  removeFavorite: (appId: string) => Promise<void>;

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
  initialized: false,
  apps: [],
  routes: [],
  favorites: [],
  notifications: [],
  addFavorite: async () => {},
  removeFavorite: async () => {},
  markNotificationRead: async () => {},
  markAllNotificationsRead: async () => {},
  login: () => {},
  logout: () => {},
  reload: async () => {},
  refreshToken: async () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  const [token, setToken] = useState<string | undefined>();
  const [user, setUser] = useState<MeResponse | undefined>();
  const [apps, setApps] = useState<AppItem[]>([]);
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [dashboard, setDashboard] =
    useState<DashboardResponse | undefined>();
  const [notifications, setNotifications] =
    useState<NotificationItem[]>([]);
  const [favorites, setFavorites] =
    useState<FavoriteAppItem[]>([]);

  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
    null
  );

  const buildCoreApi = useCallback(() => {
    const apiClient = new ApiClient("", () => keycloak.token);
    return new CoreApi(apiClient);
  }, []);

  // =====================================================
  // CORE LOAD (robusto + race-safe)
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
      favoritesData,
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
    setFavorites(favoritesData);
  }, [buildCoreApi]);

  // =====================================================
  // FAVORITES (sincronização garantida)
  // =====================================================

  const addFavorite = useCallback(
    async (appId: string) => {
      const coreApi = buildCoreApi();

      // optimistic update
      setFavorites((prev) => {
        if (prev.find((f) => f.id === appId)) return prev;

        const app = apps.find((a) => a.id === appId);
        if (!app) return prev;

        return [
          ...prev,
          {
            id: app.id,
            name: app.name,
            base_path: app.basePath,
            icon: app.icon ?? undefined,
            order_index: prev.length,
          },
        ];
      });

      await coreApi.addFavoriteApp(appId);

      // 🔥 sincroniza com backend
      await loadCoreData();
    },
    [apps, buildCoreApi, loadCoreData]
  );

  const removeFavorite = useCallback(
    async (appId: string) => {
      const coreApi = buildCoreApi();

      // optimistic update
      setFavorites((prev) =>
        prev.filter((f) => f.id !== appId)
      );

      await coreApi.removeFavoriteApp(appId);

      // 🔥 sincroniza
      await loadCoreData();
    },
    [buildCoreApi, loadCoreData]
  );

  // =====================================================
  // NOTIFICATIONS
  // =====================================================

  const markNotificationRead = useCallback(
    async (id: string) => {
      const coreApi = buildCoreApi();

      await coreApi.markNotificationRead(id);

      setNotifications((prev) =>
        prev.map((n) =>
          n.id === id ? { ...n, read: true } : n
        )
      );
    },
    [buildCoreApi]
  );

  const markAllNotificationsRead = useCallback(
    async () => {
      const coreApi = buildCoreApi();

      await coreApi.markAllNotificationsRead();

      setNotifications((prev) =>
        prev.map((n) => ({ ...n, read: true }))
      );
    },
    [buildCoreApi]
  );

  // =====================================================
  // SOCKET (recarrega com segurança)
  // =====================================================

  useSocket({
    token:
      !loading && isAuthenticated && token
        ? token
        : undefined,
    onConnected: async () => {
      await loadCoreData();
    },
    onNotification: (data) => {
      setNotifications((prev) => [data, ...prev]);
    },
    onAdminChanged: async () => {
      await loadCoreData();
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
  }, [token]);

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
    let mounted = true;

    const init = async () => {
      const authenticated = await initKeycloak();

      if (!mounted) return;

      setIsAuthenticated(authenticated);
      setToken(keycloak.token);

      if (authenticated) {
        await loadCoreData();
      }

      startTokenRefresh();
      setLoading(false);
      setInitialized(true);
    };

    init();

    return () => {
      mounted = false;
      if (refreshIntervalRef.current)
        clearInterval(refreshIntervalRef.current);
    };
  }, [loadCoreData]);

  const login = () => keycloak.login();
  const logout = () => keycloak.logout();

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        loading,
        initialized,
        token,
        user,
        apps,
        routes,
        dashboard,
        favorites,
        notifications,
        addFavorite,
        removeFavorite,
        markNotificationRead,
        markAllNotificationsRead,
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