const API_BASE = "/apps/api-delpi";

export type PublicDenunciaPayload = {
  description: string;
  website?: string;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export async function submitPublicDenuncia(
  payload: PublicDenunciaPayload,
): Promise<{ id: string | null }> {
  const response = await fetch(`${API_BASE}/public/canal-denuncia/denuncias`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let message = "Não foi possível enviar a denúncia.";
    try {
      const body = (await response.json()) as { message?: string };
      if (body.message) message = body.message;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  const envelope = (await response.json()) as ApiEnvelope<{ id: string | null }>;
  if (envelope.success === false) {
    throw new Error(envelope.message || "Não foi possível enviar a denúncia.");
  }
  return { id: envelope.data?.id ?? null };
}
