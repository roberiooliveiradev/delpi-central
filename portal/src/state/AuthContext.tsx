// src/state/AuthContext.tsx

import React, { createContext, useEffect, useState, useRef } from "react";
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
} from "../data/coreApi";

interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  token?: string;
  user?: MeResponse;
  apps: AppItem[];
  routes: RouteItem[];
  dashboard?: DashboardResponse;
  notifications: NotificationItem[];
  markNotificationRead: (id: string) => Promise<void>;
  markAllNotificationsRead: () => Promise<void>;
  login: () => void;
  logout: () => void;
  reload: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  loading: true,
  apps: [],
  routes: [],
  notifications: [],
  markNotificationRead: async () => {},
  markAllNotificationsRead: async () => {},
  login: () => {},
  logout: () => {},
  reload: async () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | undefined>();
  const [user, setUser] = useState<MeResponse | undefined>();
  const [apps, setApps] = useState<AppItem[]>([]);
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [dashboard, setDashboard] = useState<DashboardResponse | undefined>();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const initializedRef = useRef(false);

  // =========================================================
  // API HELPERS
  // =========================================================

  const buildCoreApi = () => {
    const apiClient = new ApiClient("", () => keycloak.token);
    return new CoreApi(apiClient);
  };

  const loadCoreData = async () => {
    if (!keycloak.token) return;

    try {
      const coreApi = buildCoreApi();

      const [
        me,
        appsResponse,
        routesResponse,
        dashboardData,
        notificationsData,
      ] = await Promise.all([
        coreApi.getMe(),
        coreApi.getApps(),
        coreApi.getRoutes(),
        coreApi.getDashboard(),
        coreApi.getNotifications(),
      ]);

      setUser(me);
      setApps(appsResponse);
      setRoutes(routesResponse);
      setDashboard(dashboardData);
      setNotifications(notificationsData);
    } catch (error) {
      console.error("Erro ao carregar dados da Core:", error);
    }
  };

  // =========================================================
  // NOTIFICATIONS
  // =========================================================

  const markNotificationRead = async (id: string) => {
    try {
      const coreApi = buildCoreApi();
      await coreApi.markNotificationRead(id);

      setNotifications((prev) =>
        prev.map((n) =>
          n.id === id ? { ...n, read: true } : n
        )
      );
    } catch (error) {
      console.error("Erro ao marcar notificação:", error);
    }
  };

  const markAllNotificationsRead = async () => {
    try {
      const coreApi = buildCoreApi();
      await coreApi.markAllNotificationsRead();

      setNotifications((prev) =>
        prev.map((n) => ({ ...n, read: true }))
      );
    } catch (error) {
      console.error("Erro ao marcar todas notificações:", error);
    }
  };

  // =========================================================
  // SOCKET
  // =========================================================

  useSocket({
    token,
    onConnected: async () => {
      console.log("🔄 Socket conectado → sincronizando notificações");
      await loadCoreData();
    },
    onNotification: (data) => {
      setNotifications((prev) => [data, ...prev]);
    },
  });

  // =========================================================
  // AUTH INIT
  // =========================================================

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
      .catch((err) => {
        console.error("Erro ao inicializar Keycloak:", err);
      })
      .finally(() => {
        setLoading(false);
      });

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  const startTokenRefresh = () => {
    refreshIntervalRef.current = setInterval(() => {
      keycloak
        .updateToken(60)
        .then((refreshed) => {
          if (refreshed) {
            setToken(keycloak.token);
          }
        })
        .catch(() => {
          keycloak.logout();
        });
    }, 60000);
  };

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
        notifications,
        markNotificationRead,
        markAllNotificationsRead,
        login,
        logout,
        reload: loadCoreData,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
