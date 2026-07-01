import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import { AuthContext } from "../state/AuthContext";
import {
  FALLBACK_NOTIFICATION_CATALOG,
  normalizeNotificationCatalogResponse,
  type NotificationCatalogResponse,
} from "../utils/notificationCatalog";

type NotificationCatalogContextValue = {
  catalog: NotificationCatalogResponse;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
};

const NotificationCatalogContext = createContext<NotificationCatalogContextValue>({
  catalog: FALLBACK_NOTIFICATION_CATALOG,
  loading: false,
  error: null,
  reload: async () => undefined,
});

type Props = {
  children: ReactNode;
};

export function NotificationCatalogProvider({ children }: Props) {
  const { isAuthenticated, initialized, getAccessToken, refreshToken } = useContext(AuthContext);
  const [catalog, setCatalog] = useState<NotificationCatalogResponse>(FALLBACK_NOTIFICATION_CATALOG);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const coreApi = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  const reload = useCallback(async () => {
    if (!isAuthenticated) {
      setCatalog(FALLBACK_NOTIFICATION_CATALOG);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await coreApi.getNotificationCatalog();
      setCatalog(normalizeNotificationCatalogResponse(data));
    } catch (err) {
      setCatalog(FALLBACK_NOTIFICATION_CATALOG);
      setError(err instanceof Error ? err.message : "Falha ao carregar catálogo de notificações");
    } finally {
      setLoading(false);
    }
  }, [coreApi, isAuthenticated]);

  useEffect(() => {
    if (!initialized) {
      return;
    }
    void reload();
  }, [initialized, reload]);

  const value = useMemo(
    () => ({
      catalog,
      loading,
      error,
      reload,
    }),
    [catalog, loading, error, reload],
  );

  return (
    <NotificationCatalogContext.Provider value={value}>
      {children}
    </NotificationCatalogContext.Provider>
  );
}

export function useNotificationCatalog() {
  return useContext(NotificationCatalogContext);
}
