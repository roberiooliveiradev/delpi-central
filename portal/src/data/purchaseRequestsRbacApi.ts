import { ApiClient } from "./apiClient";

type Envelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export type UserProtheusMapping = {
  user_id: string;
  protheus_user_id?: string | null;
  protheus_user_code?: string | null;
  mapping_status: string;
  mapping_source?: string | null;
  verified: boolean;
  created_at?: string;
  updated_at?: string;
};

export type ProtheusUserMatch = {
  protheus_user_id: string;
  code?: string | null;
  name?: string | null;
  email?: string | null;
};

const API_BASE = "/apps/purchase-requests-api/purchase-requests/rbac";

function unwrap<T>(body: Envelope<T>): T {
  if (!body.success) {
    throw new Error(body.message || "Erro na API de solicitações de compra.");
  }
  return body.data;
}

export class PurchaseRequestsRbacApi {
  constructor(private readonly client: ApiClient) {}

  async getUserProtheusMapping(userId: string): Promise<UserProtheusMapping | null> {
    const body = await this.client.get<Envelope<{ mapping: UserProtheusMapping | null }>>(
      `${API_BASE}/user-protheus-mappings/${encodeURIComponent(userId)}`,
    );
    return unwrap(body).mapping ?? null;
  }

  async syncUserProtheusMappingByEmail(
    userId: string,
    email: string,
    portalUserName?: string | null,
  ): Promise<{
    mapping: UserProtheusMapping;
    protheus_user: ProtheusUserMatch;
    synced_by_email: string;
  }> {
    const body = await this.client.post<
      Envelope<{
        mapping: UserProtheusMapping;
        protheus_user: ProtheusUserMatch;
        synced_by_email: string;
      }>
    >(`${API_BASE}/user-protheus-mappings/${encodeURIComponent(userId)}/sync-by-email`, {
      email,
      portal_user_name: portalUserName ?? null,
    });
    return unwrap(body);
  }
}
