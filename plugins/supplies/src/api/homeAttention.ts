import { httpGet, suppliesApiUrl } from "./httpClient";

export type HomeAttentionCardStatus = "available" | "unavailable";

export type HomeAttentionCard = {
  id: string;
  viewId: string;
  title: string;
  description: string;
  requiredCap: string;
  count: number | null;
  status: HomeAttentionCardStatus;
};

export type HomeAttentionPartialFailure = {
  source?: string;
  message?: string;
  code?: string;
};

export type HomeAttentionResponse = {
  cards: HomeAttentionCard[];
  partialFailures: HomeAttentionPartialFailure[];
};

export function getHomeAttention(signal?: AbortSignal): Promise<HomeAttentionResponse> {
  return httpGet<HomeAttentionResponse>(suppliesApiUrl("/home/attention"), { signal });
}
