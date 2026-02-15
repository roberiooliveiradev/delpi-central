// src/state/AuthContext.tsx
import React, { createContext, useEffect, useState } from "react";
import keycloak from "../data/keycloakClient";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import type { MeResponse, AppItem, RouteItem } from "../data/coreApi";
import type { DashboardResponse } from "../data/coreApi";


interface AuthContextType {
  isAuthenticated: boolean;
  token: string | undefined;
  user?: MeResponse;
  apps: AppItem[];
  routes: RouteItem[];
  dashboard?: DashboardResponse;
  login: () => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  token: undefined,
  user: undefined,
  apps: [],
  routes: [],
  dashboard: undefined,
  login: () => {},
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | undefined>(undefined);
  const [user, setUser] = useState<MeResponse | undefined>();
  const [apps, setApps] = useState<AppItem[]>([]);
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [dashboard, setDashboard] = useState<DashboardResponse | undefined>();

  useEffect(() => {
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
      .catch(() => {
        console.error("Erro ao inicializar Keycloak");
      });
  }, []);

  const loadCoreData = async () => {
    if (!keycloak.token) return;

    const apiClient = new ApiClient("", () => keycloak.token);
    const coreApi = new CoreApi(apiClient);
    
    try {
      const dashboardData = await coreApi.getDashboard();
      setDashboard(dashboardData);
      
      const me = await coreApi.getMe();
      const appsResponse = await coreApi.getApps();
      const routesResponse = await coreApi.getRoutes();

      setUser(me);
      setApps(appsResponse);
      setRoutes(routesResponse);
    } catch (error) {
      console.error("Erro ao carregar dados da Core:", error);
    }
  };

  const startTokenRefresh = () => {
    setInterval(() => {
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
        token,
        user,
        apps,
        routes,
        dashboard,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
