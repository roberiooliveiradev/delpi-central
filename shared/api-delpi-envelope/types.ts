/**
 * Contrato HTTP da api-delpi (Playbook 10).
 * Espelhar em plugins que consomem a API — ver api-delpi/docs/api/00-visao-geral.md.
 */

export type ApiDelpiResponseMeta = {
  dataVersion?: string;
  operationId?: string;
  entity?: string;
  shape?: string;
  pagination?: Record<string, unknown>;
  fields?: Record<string, string>;
  relatedRoutes?: Record<string, string>;
  sections?: Array<Record<string, unknown>>;
};

export type ApiDelpiErrorPayload = {
  code?: string;
  recoverable?: boolean;
};

export type ApiDelpiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: ApiDelpiResponseMeta;
  error?: ApiDelpiErrorPayload | null;
};

/** Alias legado nos dashboards MFE. */
export type ApiSuccessResponse<T> = ApiDelpiEnvelope<T>;

export function unwrapApiDelpiEnvelope<T>(
  response: ApiDelpiEnvelope<T>,
  fallbackMessage: string,
): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}
