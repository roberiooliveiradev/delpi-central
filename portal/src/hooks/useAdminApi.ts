import { useContext, useMemo } from "react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { AdminApi } from "../data/adminApi";

/**
 * Cliente autenticado da Admin API com refresh automático em 401.
 * Preferir este hook a `new AdminApi(new ApiClient("", getAccessToken))` —
 * sem refresh, o polling do painel de estatísticas falha quando o access token expira.
 */
export function useAdminApi(): AdminApi {
  const { getAccessToken, refreshToken } = useContext(AuthContext);

  return useMemo(
    () =>
      new AdminApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );
}
