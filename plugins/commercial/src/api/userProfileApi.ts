import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { commercialApiUrl, httpGet } from "./httpClient";

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
  phone_e164?: string | null;
  mobile_e164?: string | null;
  whatsapp_e164?: string | null;
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

/** Identidade (foto/cargo/contatos) é escrita no Meu Perfil da Minha DELPI (`/profile`). */
export function userProfilePhotoAbsoluteUrl(userId: string): string {
  return commercialApiUrl(`/users/${encodeURIComponent(userId)}/profile/photo`);
}
