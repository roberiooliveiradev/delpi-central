/** Alinhado a shared/api-delpi-envelope/types.ts */

export type ApiDelpiResponseMeta = {
  dataVersion?: string;
  operationId?: string;
  entity?: string;
  shape?: string;
};

export type ApiSuccessResponse<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: ApiDelpiResponseMeta;
};

export function unwrapApiDelpiEnvelope<T>(
  response: ApiSuccessResponse<T>,
  fallbackMessage: string,
): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}
