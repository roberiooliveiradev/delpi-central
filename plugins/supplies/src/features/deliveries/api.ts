import { httpGet, suppliesApiUrl } from "../../api/httpClient";
import type { DeliveryLateListResponse, DeliveriesQuery } from "./types";
import { buildListSearchParams } from "./query";

export async function listLateDeliveries(
  query: DeliveriesQuery,
  signal?: AbortSignal,
): Promise<DeliveryLateListResponse> {
  const qs = buildListSearchParams(query).toString();
  return httpGet<DeliveryLateListResponse>(
    suppliesApiUrl(`/deliveries/late?${qs}`),
    { signal },
  );
}
