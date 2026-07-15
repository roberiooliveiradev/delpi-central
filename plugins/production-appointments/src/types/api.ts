export type ApiDelpiEnvelope<T> = {
  success: boolean;
  data: T;
  meta?: Record<string, unknown>;
  error?: { code?: string; message?: string };
};

export function unwrapApiDelpiEnvelope<T>(payload: unknown): T {
  if (!payload || typeof payload !== "object") {
    throw new Error("Resposta inválida da API.");
  }

  const envelope = payload as ApiDelpiEnvelope<T>;

  if (envelope.success === false) {
    throw new Error(envelope.error?.message ?? "Falha ao consultar a API.");
  }

  if (!("data" in envelope)) {
    throw new Error("Resposta da API sem campo data.");
  }

  return envelope.data;
}
