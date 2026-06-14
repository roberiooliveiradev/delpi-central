export type ApiSuccessResponse<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: Record<string, unknown>;
  error?: {
    code?: string;
    recoverable?: boolean;
  };
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
