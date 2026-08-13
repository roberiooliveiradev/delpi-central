import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import {
  commercialApiUrl,
  httpDelete,
  httpGet,
  httpPatch,
  httpPutFormData,
} from "./httpClient";

export type UserProfilePortfolioDto = {
  id: string;
  name: string;
  active: boolean;
  user_id: string;
  owner_user_id?: string | null;
  role?: "owner" | "member" | string;
  customer_count?: number;
  member_count?: number;
};

export type UserProfileGroupDto = {
  id: string;
  kind: string;
  name: string;
  active: boolean;
  sort_order?: number;
};

export type UserProfileDto = {
  user_id: string;
  name: string;
  email: string;
  job_title?: string | null;
  has_photo?: boolean;
  photo_url?: string | null;
  portfolios: UserProfilePortfolioDto[];
  groups?: UserProfileGroupDto[];
  updated_at?: string | null;
};

export async function getUserProfile(
  userId: string,
  signal?: AbortSignal,
): Promise<UserProfileDto> {
  const response = await httpGet<ApiSuccessResponse<UserProfileDto>>(
    commercialApiUrl(`/users/${encodeURIComponent(userId)}/profile`),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar perfil do usuário.");
}

export async function patchUserProfile(
  userId: string,
  body: { job_title?: string | null },
  signal?: AbortSignal,
): Promise<UserProfileDto> {
  const response = await httpPatch<ApiSuccessResponse<UserProfileDto>>(
    commercialApiUrl(`/users/${encodeURIComponent(userId)}/profile`),
    body,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao atualizar perfil.");
}

export async function uploadUserProfilePhoto(
  userId: string,
  file: File,
  signal?: AbortSignal,
): Promise<UserProfileDto> {
  const form = new FormData();
  form.append("file", file);
  const response = await httpPutFormData<ApiSuccessResponse<UserProfileDto>>(
    commercialApiUrl(`/users/${encodeURIComponent(userId)}/profile/photo`),
    form,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao enviar foto.");
}

export async function deleteUserProfilePhoto(
  userId: string,
  signal?: AbortSignal,
): Promise<UserProfileDto> {
  const response = await httpDelete<ApiSuccessResponse<UserProfileDto>>(
    commercialApiUrl(`/users/${encodeURIComponent(userId)}/profile/photo`),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao remover foto.");
}

export function userProfilePhotoAbsoluteUrl(userId: string): string {
  return commercialApiUrl(`/users/${encodeURIComponent(userId)}/profile/photo`);
}
