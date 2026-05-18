// src/state/AuthContext.tsx
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

  getAccessToken: () => string | undefined;

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
  deleteNotification: (id: string) => Promise<void>;
  setNotificationImportant: (id: string, isImportant: boolean) => Promise<void>;
  reloadNotifications: () => Promise<void>;

  login: () => void;
  logout: () => void;
  reload: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const DEFAULT_FRONT_CHANNEL_LOGOUT_URLS = [
  "https://rhdelpi.minhadelpi.com.br/integracao/logout-pelo-portal-mae/",
  "https://controle-mp.minhadelpi.com.br/sso/logout-from-parent",
];

const FRONT_CHANNEL_LOGOUT_TIMEOUT_MS = 900;

/**
 * Permite evoluir o logout global sem alterar código a cada novo app.
 *
 * Exemplo:
 * VITE_FRONT_CHANNEL_LOGOUT_URLS=https://app1/logout-from-parent,https://app2/logout-from-parent
 */
function getFrontChannelLogoutUrls(): string[] {
  const raw = import.meta.env.VITE_FRONT_CHANNEL_LOGOUT_URLS;

  if (!raw || typeof raw !== "string") {
    return DEFAULT_FRONT_CHANNEL_LOGOUT_URLS;
  }

  const urls = raw
    .split(",")
    .map((url) => url.trim())
    .filter(Boolean);

  return urls.length > 0 ? urls : DEFAULT_FRONT_CHANNEL_LOGOUT_URLS;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  loading: true,
  initialized: false,
  coreLoaded: false,

  getAccessToken: () => undefined,

  apps: [],
  routes: [],
  favorites: [],
  notifications: [],

  addFavorite: async () => {},
  removeFavorite: async () => {},
  markNotificationRead: async () => {},
  markAllNotificationsRead: async () => {},
  deleteNotification: async () => {},
  setNotificationImportant: async () => {},
  reloadNotifications: async () => {},

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

  const tokenRef = useRef<string | undefined>(undefined);

  const [user, setUser] = useState<MeResponse | undefined>();
  const [apps, setApps] = useState<AppItem[]>([]);
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [dashboard, setDashboard] = useState<DashboardResponse | undefined>();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [favorites, setFavorites] = useState<FavoriteAppItem[]>([]);

  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const refreshPromiseRef = useRef<Promise<boolean> | null>(null);

  const identityLoadInFlightRef = useRef(false);
  const dashboardLoadInFlightRef = useRef(false);
  const notificationsLoadInFlightRef = useRef(false);
  const favoritesLoadInFlightRef = useRef(false);
  const unauthorizedHandledRef = useRef(false);

  const getCurrentRedirectUri = () => window.location.href;

  const getAccessToken = useCallback(() => tokenRef.current, []);

  const clearSessionState = useCallback(() => {
    setIsAuthenticated(false);
    setCoreLoaded(false);

    tokenRef.current = undefined;

    setUser(undefined);
    setApps([]);
    setRoutes([]);
    setDashboard(undefined);
    setNotifications([]);
    setFavorites([]);

    identityLoadInFlightRef.current = false;
    dashboardLoadInFlightRef.current = false;
    notificationsLoadInFlightRef.current = false;
    favoritesLoadInFlightRef.current = false;
  }, []);

  const stopTokenRefresh = useCallback(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }
  }, []);

  const runFrontChannelLogout = useCallback(
    (url: string, timeoutMs = FRONT_CHANNEL_LOGOUT_TIMEOUT_MS): Promise<void> => {
      return new Promise((resolve) => {
        const iframe = document.createElement("iframe");
        let finished = false;

        const finish = () => {
          if (finished) return;
          finished = true;

          try {
            iframe.remove();
          } catch {
            // noop
          }

          resolve();
        };

        iframe.style.display = "none";
        iframe.referrerPolicy = "strict-origin-when-cross-origin";
        iframe.src = url;

        iframe.onload = () => {
          window.setTimeout(finish, 150);
        };

        iframe.onerror = () => {
          finish();
        };

        document.body.appendChild(iframe);
        window.setTimeout(finish, timeoutMs);
      });
    },
    []
  );

  const runGlobalFrontChannelLogout = useCallback(async () => {
    const urls = getFrontChannelLogoutUrls();

    await Promise.allSettled(
      urls.map((url) => runFrontChannelLogout(url))
    );
  }, [runFrontChannelLogout]);

  const handleUnauthorized = useCallback(async () => {
    if (unauthorizedHandledRef.current) return;
    unauthorizedHandledRef.current = true;

    stopTokenRefresh();

    try {
      await keycloak.login({ redirectUri: getCurrentRedirectUri() });
    } finally {
      unauthorizedHandledRef.current = false;
    }
  }, [stopTokenRefresh]);

  const refreshTokenSilently = useCallback(async (): Promise<boolean> => {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    refreshPromiseRef.current = (async () => {
      try {
        const currentToken = tokenRef.current;
        const refreshed = await keycloak.updateToken(60);
        const nextToken = keycloak.token;

        if (nextToken && nextToken !== currentToken) {
          tokenRef.current = nextToken;
        }

        return refreshed || !!nextToken;
      } catch {
        return false;
      } finally {
        refreshPromiseRef.current = null;
      }
    })();

    return refreshPromiseRef.current;
  }, []);

  const refreshToken = useCallback(async () => {
    const refreshed = await refreshTokenSilently();

    if (!refreshed) {
      await handleUnauthorized();
    }
  }, [refreshTokenSilently, handleUnauthorized]);

  const buildCoreApi = useCallback(() => {
    const apiClient = new ApiClient("", () => tokenRef.current, {
      refreshToken: refreshTokenSilently,
      onUnauthorized: handleUnauthorized,
    });

    return new CoreApi(apiClient);
  }, [refreshTokenSilently, handleUnauthorized]);

  const loadIdentityAndNavigation = useCallback(async () => {
    if (!tokenRef.current) return;
    if (identityLoadInFlightRef.current) return;

    identityLoadInFlightRef.current = true;

    try {
      const coreApi = buildCoreApi();

      const [me, appsResponse] = await Promise.all([
        coreApi.getMe(),
        coreApi.getApps(),
      ]);

      setUser(me);
      setApps(appsResponse);

      const derivedRoutes = appsResponse.flatMap((app) => app.routes ?? []);
      setRoutes(derivedRoutes);
    } finally {
      identityLoadInFlightRef.current = false;
    }
  }, [buildCoreApi]);

  const loadDashboardData = useCallback(async () => {
    if (!tokenRef.current) return;
    if (dashboardLoadInFlightRef.current) return;

    dashboardLoadInFlightRef.current = true;

    try {
      const coreApi = buildCoreApi();
      const dashboardData = await coreApi.getDashboard();
      setDashboard(dashboardData);
    } finally {
      dashboardLoadInFlightRef.current = false;
    }
  }, [buildCoreApi]);

  const loadNotificationsData = useCallback(async () => {
    if (!tokenRef.current) return;
    if (notificationsLoadInFlightRef.current) return;

    notificationsLoadInFlightRef.current = true;

    try {
      const coreApi = buildCoreApi();
      const notificationsData = await coreApi.getNotifications();
      setNotifications(notificationsData);
    } finally {
      notificationsLoadInFlightRef.current = false;
    }
  }, [buildCoreApi]);

  const loadFavoritesData = useCallback(async () => {
    if (!tokenRef.current) return;
    if (favoritesLoadInFlightRef.current) return;

    favoritesLoadInFlightRef.current = true;

    try {
      const coreApi = buildCoreApi();
      const favoritesData = await coreApi.getFavoriteApps();
      setFavorites(favoritesData);
    } finally {
      favoritesLoadInFlightRef.current = false;
    }
  }, [buildCoreApi]);

  const loadCoreData = useCallback(async () => {
    if (!tokenRef.current) return;

    await Promise.all([
      loadIdentityAndNavigation(),
      loadDashboardData(),
      loadNotificationsData(),
      loadFavoritesData(),
    ]);

    setCoreLoaded(true);
  }, [
    loadIdentityAndNavigation,
    loadDashboardData,
    loadNotificationsData,
    loadFavoritesData,
  ]);

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
      await loadFavoritesData();
    },
    [apps, buildCoreApi, loadFavoritesData]
  );

  const removeFavorite = useCallback(
    async (appId: string) => {
      const coreApi = buildCoreApi();

      setFavorites((prev) => prev.filter((f) => f.id !== appId));

      await coreApi.removeFavoriteApp(appId);
      await loadFavoritesData();
    },
    [buildCoreApi, loadFavoritesData]
  );

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

  const deleteNotification = useCallback(
    async (id: string) => {
      const coreApi = buildCoreApi();
      await coreApi.deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    },
    [buildCoreApi],
  );

  const setNotificationImportant = useCallback(
    async (id: string, isImportant: boolean) => {
      const coreApi = buildCoreApi();
      await coreApi.setNotificationImportant(id, isImportant);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isImportant } : n)),
      );
    },
    [buildCoreApi],
  );

  const startTokenRefresh = useCallback(() => {
    if (refreshIntervalRef.current) return;

    refreshIntervalRef.current = setInterval(() => {
      void refreshToken();
    }, 60000);
  }, [refreshToken]);

  useSocket({
    token: !loading && isAuthenticated ? tokenRef.current : undefined,
    onConnected: async () => {
      await Promise.all([loadIdentityAndNavigation(), loadNotificationsData()]);
    },
    onNotification: (data) => {
      setNotifications((prev) => [data, ...prev]);
    },
    onAdminChanged: async (data) => {
      if (data?.entity === "notifications") {
        await loadNotificationsData();
        return;
      }

      await loadIdentityAndNavigation();
    },
  });

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      try {
        const authenticated = await initKeycloak();
        if (!mounted) return;

        setIsAuthenticated(authenticated);

        if (authenticated && keycloak.token) {
          tokenRef.current = keycloak.token;

          await loadCoreData();
          startTokenRefresh();
        }

        setLoading(false);
        setInitialized(true);
      } catch {
        if (!mounted) return;

        clearSessionState();
        setLoading(false);
        setInitialized(true);
      }
    };

    void init();

    return () => {
      mounted = false;
      stopTokenRefresh();
    };
  }, [clearSessionState, loadCoreData, startTokenRefresh, stopTokenRefresh]);

  const login = useCallback(() => {
    void keycloak.login({ redirectUri: getCurrentRedirectUri() });
  }, []);

  const logout = useCallback(() => {
    /**
     * Evento local para componentes/microfrontends já carregados dentro da Minha DELPI.
     * Ex.: AppHost pode repassar DELPI_LOGOUT para iframes ou remotes montados.
     */
    window.dispatchEvent(new CustomEvent("DELPI_GLOBAL_LOGOUT"));

    stopTokenRefresh();

    window.setTimeout(() => {
      clearSessionState();

      void runGlobalFrontChannelLogout().finally(() => {
        void keycloak.logout({ redirectUri: window.location.origin + "/" });
      });
    }, 150);
  }, [clearSessionState, stopTokenRefresh, runGlobalFrontChannelLogout]);

  const contextValue = useMemo<AuthContextType>(
    () => ({
      isAuthenticated,
      loading,
      initialized,
      coreLoaded,

      getAccessToken,
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
      deleteNotification,
      setNotificationImportant,
      reloadNotifications: loadNotificationsData,

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
      getAccessToken,
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
      deleteNotification,
      setNotificationImportant,
      loadNotificationsData,
      login,
      logout,
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