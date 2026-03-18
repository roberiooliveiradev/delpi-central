// src/hooks/useDelpiApi.ts
import { useContext, useMemo } from "react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { DelpiApi } from "../data/delpiApi";

export const useDelpiApi = () => {
  const { getAccessToken, refreshToken } = useContext(AuthContext);

  return useMemo(() => {
    const client = new ApiClient("", getAccessToken, {
      refreshToken: async () => {
        await refreshToken();
        return Boolean(getAccessToken());
      },
    });

    return new DelpiApi(client);
  }, [getAccessToken, refreshToken]);
};