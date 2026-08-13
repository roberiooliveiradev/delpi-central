import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { commercialApiUrl, httpDelete, httpGet, httpPost, httpPut } from "./httpClient";

export type CommercialGroupMemberDto = {
  user_id: string;
};

export type CommercialGroupDto = {
  id: string;
  kind: string;
  name: string;
  active: boolean;
  sort_order: number;
  member_count: number;
  members: CommercialGroupMemberDto[];
};

export async function listCommercialGroups(
  options?: { activeOnly?: boolean; signal?: AbortSignal },
): Promise<CommercialGroupDto[]> {
  const params = new URLSearchParams();
  if (options?.activeOnly) params.set("active_only", "true");
  const qs = params.toString();
  const response = await httpGet<ApiSuccessResponse<{ items: CommercialGroupDto[] }>>(
    `${commercialApiUrl("/groups")}${qs ? `?${qs}` : ""}`,
    { signal: options?.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao listar grupos.");
  return data.items ?? [];
}

export async function getCommercialGroup(
  groupId: string,
  signal?: AbortSignal,
): Promise<CommercialGroupDto> {
  const response = await httpGet<ApiSuccessResponse<CommercialGroupDto>>(
    commercialApiUrl(`/groups/${encodeURIComponent(groupId)}`),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar grupo.");
}

export async function addCommercialGroupMember(
  groupId: string,
  userId: string,
): Promise<CommercialGroupDto> {
  const response = await httpPost<ApiSuccessResponse<CommercialGroupDto>>(
    commercialApiUrl(`/groups/${encodeURIComponent(groupId)}/members`),
    { user_id: userId },
  );
  return unwrapEnvelope(response, "Erro ao adicionar membro ao grupo.");
}

export async function removeCommercialGroupMember(
  groupId: string,
  userId: string,
): Promise<CommercialGroupDto> {
  const response = await httpDelete<ApiSuccessResponse<CommercialGroupDto>>(
    commercialApiUrl(
      `/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}`,
    ),
  );
  return unwrapEnvelope(response, "Erro ao remover membro do grupo.");
}

export async function replaceCommercialGroupMembers(
  groupId: string,
  userIds: string[],
): Promise<CommercialGroupDto> {
  const response = await httpPut<ApiSuccessResponse<CommercialGroupDto>>(
    commercialApiUrl(`/groups/${encodeURIComponent(groupId)}/members`),
    { user_ids: userIds },
  );
  return unwrapEnvelope(response, "Erro ao atualizar membros do grupo.");
}
