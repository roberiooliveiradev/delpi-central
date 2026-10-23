import { httpGet, suppliesApiUrl } from "./httpClient";

export type HomeAttentionCardStatus = "available" | "unavailable";

export type HomeAttentionTarget =
  | { kind: "view"; viewId: string; query?: string | null }
  | { kind: "href"; href: string };

export type HomeAttentionCard = {
  id: string;
  title: string;
  description: string;
  count: number | null;
  countUnit?: string | null;
  status: HomeAttentionCardStatus;
  target?: HomeAttentionTarget | null;
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
