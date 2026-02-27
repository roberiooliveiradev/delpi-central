// src/state/AuthContext.tsx

import React, { createContext, useEffect, useState, useRef, useCallback } from "react";
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
  refreshToken: () => Promise<void>; // 🔥 NOVO
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
  refreshToken: async () => {}, // 🔥 NOVO
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | undefined>();
  const [user, setUser] = useState<MeResponse | undefined>();
  const [apps, setApps] = useState<AppItem[]>([]);
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [dashboard, setDashboard] = useState<DashboardResponse | undefined>();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [favorites, setFavorites] = useState<FavoriteAppItem[]>([]);

  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const initializedRef = useRef(false);

  const buildCoreApi = useCallback(() => {
    const apiClient = new ApiClient("", () => keycloak.token);
    return new CoreApi(apiClient);
  }, []);

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

  // 🔥 REFRESH MANUAL (usado pelo iframe)
  const refreshToken = useCallback(async () => {
    try {
      const refreshed = await keycloak.updateToken(60);
      if (refreshed) {
        setToken(keycloak.token);
      }
    } catch {
      keycloak.logout();
    }
  }, []);

  const startTokenRefresh = () => {
    refreshIntervalRef.current = setInterval(() => {
      refreshToken();
    }, 60000);
  };

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
      if (refreshIntervalRef.current) clearInterval(refreshIntervalRef.current);
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
        refreshToken, // 🔥 EXPORTADO
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};