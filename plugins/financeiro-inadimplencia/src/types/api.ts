export type ApiDelpiMeta = {
  operationId?: string;
  entity?: string;
  [key: string]: unknown;
};

export type ApiDelpiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: ApiDelpiMeta;
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};

export function unwrapApiDelpiEnvelope<T>(payload: unknown): T {
  if (!payload || typeof payload !== "object") {
    throw new Error("Resposta inválida da API.");
  }

  const envelope = payload as ApiDelpiEnvelope<T>;

  if (envelope.success === false) {
    const message =
      envelope.error?.message ??
      (typeof envelope.error === "string" ? envelope.error : null) ??
      envelope.message ??
      "Falha ao consultar a API.";
    throw new Error(message);
  }

  if (!("data" in envelope)) {
    throw new Error("Resposta da API sem campo data.");
  }

  return envelope.data;
}
