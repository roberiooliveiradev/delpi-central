// src/hooks/useDelpiApi.ts
import { useContext, useMemo } from "react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { DelpiApi } from "../data/delpiApi";

export const useDelpiApi = () => {
  const { token } = useContext(AuthContext);

  return useMemo(() => {
    if (!token) return undefined;
    const client = new ApiClient("", () => token);
    return new DelpiApi(client);
  }, [token]);
};