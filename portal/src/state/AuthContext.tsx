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
});

type AdminChangedEvent = {
  entity?: "apps" | "routes" | "rbac" | "plugins" | "dashboard" | string;
  action?: string;
  payload?: any;
};

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

  // Enterprise sync engine (coalescing + debounce + anti-race)
  const syncQueueRef = useRef<Set<string>>(new Set());
  const syncTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isSyncingRef = useRef(false);
  const pendingResyncRef = useRef(false);

  // =========================================================
  // API HELPERS
  // =========================================================

  const buildCoreApi = useCallback(() => {
    const apiClient = new ApiClient("", () => keycloak.token);
    return new CoreApi(apiClient);
  }, []);

  const loadCoreData = useCallback(async () => {
    if (!keycloak.token) return;

    try {
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
    } catch (error) {
      console.error("Erro ao carregar dados da Core:", error);
    }
  }, [buildCoreApi]);

  const runSyncBatch = useCallback(async (entities: string[]) => {
    if (!keycloak.token) return;

    const coreApi = buildCoreApi();
    const tasks: Promise<void>[] = [];

    // Plugins normalmente impactam catálogo (apps) e também rotas (se plugin publica rotas)
    const needsApps =
      entities.includes("apps") || entities.includes("plugins");
    
    const needsMe = entities.includes("rbac");
    
    const needsRoutes =
      entities.includes("routes") ||
      entities.includes("apps") ||
      entities.includes("plugins") ||
      entities.includes("rbac"); 

    const needsDashboard = entities.includes("dashboard");

    if (needsApps) {
      tasks.push(
        coreApi.getApps().then((res) => setApps(res))
      );
    }

    if (needsRoutes) {
      tasks.push(
        coreApi.getRoutes().then((res) => setRoutes(res))
      );
    }

    if (needsMe) {
      tasks.push(
        coreApi.getMe().then((res) => setUser(res))
      );
    }

    if (needsDashboard) {
      tasks.push(
        coreApi.getDashboard().then((res) => setDashboard(res))
      );
    }

    // Notifications/favorites NÃO precisam recarregar em eventos admin.changed (custoso e desnecessário).
    // Elas já são cobertas por evento "notification" e ações do usuário.

    await Promise.all(tasks);
  }, [buildCoreApi]);

  const scheduleSync = useCallback((entity: string) => {
    if (!entity) return;

    // normaliza entity desconhecida para "apps" (fallback seguro) ou simplesmente ignora:
    // aqui escolhi fallback seguro para não deixar UI desatualizada.
    const normalized = ["apps", "routes", "rbac", "plugins", "dashboard"].includes(entity)
      ? entity
      : "apps";

    syncQueueRef.current.add(normalized);

    // já existe debounce pendente
    if (syncTimeoutRef.current) return;

    syncTimeoutRef.current = setTimeout(async () => {
      syncTimeoutRef.current = null;

      // se já está sincronizando, marca pra rodar novamente ao final
      if (isSyncingRef.current) {
        pendingResyncRef.current = true;
        return;
      }

      isSyncingRef.current = true;

      try {
        // puxa o batch atual
        const entities = Array.from(syncQueueRef.current);
        syncQueueRef.current.clear();

        await runSyncBatch(entities);
        // console.log("✅ Sync granular concluído:", entities);
      } catch (err) {
        console.error("Erro no sync granular:", err);
      } finally {
        isSyncingRef.current = false;

        // se durante o sync entraram novos eventos, roda mais um batch imediatamente
        if (pendingResyncRef.current || syncQueueRef.current.size > 0) {
          pendingResyncRef.current = false;
          const entities = Array.from(syncQueueRef.current);
          syncQueueRef.current.clear();
          if (entities.length > 0) {
            try {
              isSyncingRef.current = true;
              await runSyncBatch(entities);
              // console.log("✅ Sync granular (resync) concluído:", entities);
            } catch (err) {
              console.error("Erro no sync granular (resync):", err);
            } finally {
              isSyncingRef.current = false;
            }
          }
        }
      }
    }, 120); // debounce curto para coalescer rajadas
  }, [runSyncBatch]);

  // =========================================================
  // NOTIFICATIONS
  // =========================================================

  const markNotificationRead = useCallback(async (id: string) => {
    try {
      const coreApi = buildCoreApi();
      await coreApi.markNotificationRead(id);

      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
    } catch (error) {
      console.error("Erro ao marcar notificação:", error);
    }
  }, [buildCoreApi]);

  const markAllNotificationsRead = useCallback(async () => {
    try {
      const coreApi = buildCoreApi();
      await coreApi.markAllNotificationsRead();

      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch (error) {
      console.error("Erro ao marcar todas notificações:", error);
    }
  }, [buildCoreApi]);

  // =========================================================
  // SOCKET
  // =========================================================

  useSocket({
    token,
    onConnected: async () => {
      console.log("🔄 Socket conectado → sincronizando Core");
      await loadCoreData();
    },
    onNotification: (data) => {
      setNotifications((prev) => [data, ...prev]);
    },
    onAdminChanged: (event: AdminChangedEvent) => {
      // todos usuários (não só admin) recebem e reagem
      const entity = event?.entity;
      if (!entity) return;

      // console.log("⚙️ admin.changed → scheduleSync:", entity, event?.action);
      scheduleSync(entity);
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
      if (refreshIntervalRef.current) clearInterval(refreshIntervalRef.current);
      if (syncTimeoutRef.current) clearTimeout(syncTimeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startTokenRefresh = () => {
    refreshIntervalRef.current = setInterval(() => {
      keycloak
        .updateToken(60)
        .then((refreshed) => {
          if (refreshed) setToken(keycloak.token);
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
        favorites,
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