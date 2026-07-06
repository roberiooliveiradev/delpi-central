import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type CollaborationEntityType =
  | "processo"
  | "processo_instancia"
  | "revisao"
  | "filial"
  | "setor"
  | "recurso";

export type CollaborationPresenceUser = {
  user_id?: string;
  user_name?: string;
  user_email?: string;
  section_key: string;
  mode: "viewing" | "editing";
  lock_active?: boolean;
};

export type CollaborationPresencePayload = {
  entity_type: CollaborationEntityType;
  entity_id: string;
  viewers: CollaborationPresenceUser[];
  editors: CollaborationPresenceUser[];
};

async function parseEnvelope<T>(response: Response): Promise<T> {
  const body = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !body.success) {
    throw new Error(body.message || `Erro HTTP ${response.status}`);
  }
  return body.data;
}

async function request<T>(
  path: string,
  getAccessToken?: () => string | undefined,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...buildAuthHeaders(getAccessToken),
      ...(init?.headers ?? {}),
    },
  });
  return parseEnvelope<T>(response);
}

export async function fetchCollaborationPresence(
  entityType: CollaborationEntityType,
  entityId: string,
  getAccessToken?: () => string | undefined
): Promise<CollaborationPresencePayload> {
  const query = new URLSearchParams({ entity_type: entityType, entity_id: entityId });
  return request(`/colaboracao/presenca?${query.toString()}`, getAccessToken);
}

export async function sendCollaborationHeartbeat(
  payload: {
    entity_type: CollaborationEntityType;
    entity_id: string;
    section_key: string;
    mode: "viewing" | "editing";
  },
  getAccessToken?: () => string | undefined
) {
  return request("/colaboracao/presenca", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function acquireCollaborationLock(
  payload: {
    entity_type: CollaborationEntityType;
    entity_id: string;
    section_key: string;
  },
  getAccessToken?: () => string | undefined
): Promise<{ acquired?: boolean; presence?: CollaborationPresenceUser; holder?: CollaborationPresenceUser }> {
  try {
    return await request("/colaboracao/travar", getAccessToken, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (err) {
    if (err instanceof Error && err.message.includes("Seção em edição")) {
      return { acquired: false };
    }
    throw err;
  }
}

export async function releaseCollaborationLock(
  payload: {
    entity_type: CollaborationEntityType;
    entity_id: string;
    section_key: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request("/colaboracao/liberar", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
