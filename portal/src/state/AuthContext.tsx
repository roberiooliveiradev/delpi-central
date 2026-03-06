import React, {
  createContext,
  useEffect,
  useState,
  useRef,
  useCallback,
  useMemo,
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
  coreLoaded: boolean;

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
  coreLoaded: false,

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

  const [coreLoaded, setCoreLoaded] = useState(false);

  const [token, setToken] = useState<string | undefined>();
  const tokenRef = useRef<string | undefined>(undefined);

  const [user, setUser] = useState<MeResponse | undefined>();
  const [apps, setApps] = useState<AppItem[]>([]);
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [dashboard, setDashboard] = useState<DashboardResponse | undefined>();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [favorites, setFavorites] = useState<FavoriteAppItem[]>([]);

  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const coreLoadInFlightRef = useRef(false);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const buildCoreApi = useCallback(() => {
    const apiClient = new ApiClient("", () => tokenRef.current);
    return new CoreApi(apiClient);
  }, []);

  // =====================================================
  // CORE LOAD
  // =====================================================
  const loadCoreData = useCallback(async () => {
    if (!tokenRef.current) return;
    if (coreLoadInFlightRef.current) return;

    coreLoadInFlightRef.current = true;

    try {
      const coreApi = buildCoreApi();

      const [
        me,
        appsResponse,
        dashboardData,
        notificationsData,
        favoritesData,
      ] = await Promise.all([
        coreApi.getMe(),
        coreApi.getApps(),
        coreApi.getDashboard(),
        coreApi.getNotifications(),
        coreApi.getFavoriteApps(),
      ]);

      setUser(me);
      setApps(appsResponse);

      // 🔥 Derivar rotas diretamente dos apps
      const derivedRoutes = appsResponse.flatMap((app) => app.routes ?? []);
      setRoutes(derivedRoutes);

      setDashboard(dashboardData);
      setNotifications(notificationsData);
      setFavorites(favoritesData);

      setCoreLoaded(true);
    } finally {
      coreLoadInFlightRef.current = false;
    }
  }, [buildCoreApi]);

  // =====================================================
  // FAVORITES
  // =====================================================
  const addFavorite = useCallback(
    async (appId: string) => {
      const coreApi = buildCoreApi();

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
      await loadCoreData();
    },
    [apps, buildCoreApi, loadCoreData]
  );

  const removeFavorite = useCallback(
    async (appId: string) => {
      const coreApi = buildCoreApi();

      setFavorites((prev) => prev.filter((f) => f.id !== appId));

      await coreApi.removeFavoriteApp(appId);
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
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
    },
    [buildCoreApi]
  );

  const markAllNotificationsRead = useCallback(async () => {
    const coreApi = buildCoreApi();
    await coreApi.markAllNotificationsRead();

    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, [buildCoreApi]);

  // =====================================================
  // TOKEN REFRESH
  // =====================================================
  const refreshToken = useCallback(async () => {
    try {
      const refreshed = await keycloak.updateToken(60);

      if (refreshed && keycloak.token && keycloak.token !== tokenRef.current) {
        setToken(keycloak.token);
      }
    } catch {
      keycloak.login({ redirectUri: window.location.origin + "/" });
    }
  }, []);

  const startTokenRefresh = useCallback(() => {
    if (refreshIntervalRef.current) return;

    refreshIntervalRef.current = setInterval(refreshToken, 60000);
  }, [refreshToken]);

  const stopTokenRefresh = useCallback(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }
  }, []);

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
    onAdminChanged: async () => {
      await loadCoreData();
    },
  });

  // =====================================================
  // INIT
  // =====================================================
  useEffect(() => {
    let mounted = true;

    const init = async () => {
      const authenticated = await initKeycloak();
      if (!mounted) return;

      setIsAuthenticated(authenticated);

      if (authenticated && keycloak.token) {
        setToken(keycloak.token);
      }

      setLoading(false);
      setInitialized(true);
    };

    init();

    return () => {
      mounted = false;
      stopTokenRefresh();
    };
  }, [stopTokenRefresh]);

  // =====================================================
  // TOKEN READY
  // =====================================================
  useEffect(() => {
    if (!token) return;

    loadCoreData();
    startTokenRefresh();
  }, [token, loadCoreData, startTokenRefresh]);

  const login = () =>
    keycloak.login({ redirectUri: window.location.origin + "/" });

  const logout = () => {
    stopTokenRefresh();
    keycloak.logout();
  };

  const contextValue = useMemo<AuthContextType>(
    () => ({
      isAuthenticated,
      loading,
      initialized,
      coreLoaded,

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
    }),
    [
      isAuthenticated,
      loading,
      initialized,
      coreLoaded,
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
      loadCoreData,
      refreshToken,
    ]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};