import { buildAuthHeaders } from "../../data/api/transformometroApiBase";
import type { TeoPortalContext } from "./teoPortalContext";

/**
 * Publisher do contrato transversal ``workspace_context_v1`` (Core).
 *
 * O payload é só dica de navegação — nunca autorização, nunca estado de
 * domínio, nunca dados do usuário além das refs de entidade. A identidade
 * vem do token autenticado no backend; o MFE nunca envia user_id.
 *
 * ``active`` significa "workspace aberto" (não "aba focada") — o usuário
 * conversando com o TÉO em outra aba mantém o contexto ACTIVE. ``focused``
 * é apenas evidência de foreground para desempate de ambiguidade no Core.
 */
export const WORKSPACE_CONTEXT_VERSION = 1;
export const WORKSPACE_CONTEXT_APP_ID = "transformometro";

export type WorkspaceContextEntityRef = {
  entity_type: string;
  entity_id: string;
};

export type WorkspaceContextPayloadV1 = {
  version: typeof WORKSPACE_CONTEXT_VERSION;
  app_id: typeof WORKSPACE_CONTEXT_APP_ID;
  route_id: string;
  client_instance_id: string;
  entity_refs: WorkspaceContextEntityRef[];
  presentation_state: Record<string, string | number | boolean>;
  canonical_path: string;
  active: boolean;
  focused: boolean;
  source: "mfe";
};

let cachedClientInstanceId: string | null = null;

/** Identidade estável por aba/publisher — base do desempate multi-tab. */
export function workspaceClientInstanceId(): string {
  if (!cachedClientInstanceId) {
    const rand =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    cachedClientInstanceId = `tm-${rand}`;
  }
  return cachedClientInstanceId;
}

/** Apenas testes: reinicia a identidade da aba. */
export function resetWorkspaceClientInstanceId(): void {
  cachedClientInstanceId = null;
}

/** Projeta o contexto de navegação canônico no contrato transversal. */
export function buildWorkspaceContextPayload(
  context: TeoPortalContext,
  routeView: string,
  focused: boolean,
): WorkspaceContextPayloadV1 {
  const entityRefs: WorkspaceContextEntityRef[] = [];
  if (context.process_id) {
    entityRefs.push({ entity_type: "process", entity_id: context.process_id });
  }
  if (context.instance_id) {
    entityRefs.push({ entity_type: "instance", entity_id: context.instance_id });
  }
  if (context.revision_id) {
    entityRefs.push({ entity_type: "revision", entity_id: context.revision_id });
  }
  const presentation: Record<string, string> = {};
  if (context.area) presentation.area = context.area;
  return {
    version: WORKSPACE_CONTEXT_VERSION,
    app_id: WORKSPACE_CONTEXT_APP_ID,
    route_id: routeView || "unknown",
    client_instance_id: workspaceClientInstanceId(),
    entity_refs: entityRefs,
    presentation_state: presentation,
    canonical_path: context.canonical_path,
    active: true,
    focused,
    source: "mfe",
  };
}

/** Assinatura de mudança material — dedupe evita flood HTTP por render. */
export function workspaceContextSignature(
  payload: WorkspaceContextPayloadV1,
): string {
  return JSON.stringify([
    payload.route_id,
    payload.entity_refs,
    payload.presentation_state,
    payload.canonical_path,
    payload.active,
    payload.focused,
  ]);
}

export async function publishWorkspaceContext(
  payload: WorkspaceContextPayloadV1,
  getAccessToken?: () => string | undefined,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/core-api/me/workspace-context", {
    method: "PUT",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...buildAuthHeaders(getAccessToken),
    },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok) {
    throw new Error(`workspace-context publish ${response.status}`);
  }
}

/** keepalive para unmount/pagehide — invalida o contexto desta aba. */
export function unpublishWorkspaceContext(
  getAccessToken?: () => string | undefined,
): void {
  const clientId = workspaceClientInstanceId();
  void fetch(
    `/core-api/me/workspace-context?client_instance_id=${encodeURIComponent(clientId)}`,
    {
      method: "DELETE",
      headers: buildAuthHeaders(getAccessToken),
      keepalive: true,
    },
  ).catch(() => {});
}
