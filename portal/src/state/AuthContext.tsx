// src/state/AuthContext.tsx

import React, { createContext, useEffect, useState, useRef } from "react";
import keycloak from "../data/keycloakClient";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import { io, Socket } from "socket.io-client";


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
  login: () => void;
  logout: () => void;
  reload: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  loading: true,
  token: undefined,
  user: undefined,
  apps: [],
  routes: [],
  dashboard: undefined,
  notifications: [],
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

  const socketRef = useRef<Socket | null>(null);

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

        if (authenticated && keycloak.token) {
          // 1) conecta socket ANTES
          socketRef.current = io("/", {
            path: "/socket.io",
            query: { token: keycloak.token },
            transports: ["websocket"],
          });

          socketRef.current.on("connect", () => {
            console.log("✅ WebSocket conectado:", socketRef.current?.id);
          });

          socketRef.current.on("notification", (data) => {
            console.log("📩 Notificação recebida:", data);
            setNotifications((prev) => [data, ...prev]);
          });

          socketRef.current.on("disconnect", () => {
            console.log("❌ WebSocket desconectado");
          });
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

      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };

  }, []);

  const loadCoreData = async () => {
    if (!keycloak.token) return;

    const apiClient = new ApiClient("", () => keycloak.token);
    const coreApi = new CoreApi(apiClient);

    try {
      // Paralelizar chamadas
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
        login,
        logout,
        reload: loadCoreData,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
