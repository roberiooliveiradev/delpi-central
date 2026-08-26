import { useContext, useMemo } from "react";

import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { PurchaseRequestsRbacApi } from "../data/purchaseRequestsRbacApi";

export function usePurchaseRequestsRbacApi(): PurchaseRequestsRbacApi {
  const { getAccessToken, refreshToken } = useContext(AuthContext);

  return useMemo(
    () =>
      new PurchaseRequestsRbacApi(
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
