import { useContext, useMemo } from "react";

import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";

/**
 * Authenticated Core API client with automatic 401 refresh.
 */
export function useCoreApi(): CoreApi {
  const { getAccessToken, refreshToken } = useContext(AuthContext);

  return useMemo(
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
}
