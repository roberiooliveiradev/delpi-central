import { cfApiUrl, httpGet } from "./httpClient";

export type ViewerCapabilities = {
  access: boolean;
  manage: boolean;
};

export type ViewerContext = {
  firstName: string | null;
  displayName?: string | null;
  capabilities: ViewerCapabilities;
};

type ViewerContextEnvelope = {
  success: boolean;
  data?: ViewerContext | null;
};

/**
 * GET /viewer-context — identidade e capabilities do viewer.
 * Contrato congelado IMP-MFE-HOME (D2=A): a BFF é a única fonte —
 * o MFE nunca consulta Core nem api-delpi.
 */
export async function getViewerContext(options?: {
  signal?: AbortSignal;
}): Promise<ViewerContext> {
  const envelope = await httpGet<ViewerContextEnvelope>(
    cfApiUrl("/viewer-context"),
    options,
  );
  const data = envelope?.data;
  return {
    firstName: data?.firstName ?? null,
    displayName: data?.displayName ?? null,
    capabilities: {
      access: Boolean(data?.capabilities?.access),
      manage: Boolean(data?.capabilities?.manage),
    },
  };
}
