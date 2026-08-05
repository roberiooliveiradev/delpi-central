export type ApiSuccessResponse<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export function unwrapEnvelope<T>(response: ApiSuccessResponse<T>, fallbackMessage: string): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}
