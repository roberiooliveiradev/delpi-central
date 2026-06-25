import { httpGet, unwrapApiDelpiEnvelope, type ApiEnvelope } from "./httpClient";
import type { KaizenLinkListResponse } from "../types/kaizenLink";

const API_BASE = "/apps/api-delpi/quality/kaizens/records";

export async function fetchKaizenLinkOptions(
  branchCode?: string,
): Promise<KaizenLinkListResponse> {
  const search = new URLSearchParams();
  search.set("page_size", "100");
  if (branchCode) search.set("branch", branchCode);
  const envelope = await httpGet<ApiEnvelope<KaizenLinkListResponse>>(
    `${API_BASE}?${search.toString()}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar kaizens para vínculo.");
}

export function kaizenEditPath(kaizenId: string): string {
  return `/apps/cadastro-kaizen/editar/${kaizenId}`;
}
