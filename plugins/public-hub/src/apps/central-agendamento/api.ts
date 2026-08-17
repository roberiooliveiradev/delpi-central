const API_BASE = "/apps/api-delpi";

export type PublicSchedulingResource = {
  id: string;
  branch_code: "ES" | "SC";
  name: string;
  resource_type: string;
  description: string | null;
  capacity: number | null;
  requires_approval: boolean;
};

export type BusySlot = {
  start_at: string;
  end_at: string;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

async function readError(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { message?: string };
    if (body.message) return body.message;
  } catch {
    /* ignore */
  }
  return fallback;
}

export async function fetchPublicSchedulingResource(
  token: string,
): Promise<PublicSchedulingResource> {
  const response = await fetch(
    `${API_BASE}/public/scheduling/resources/${encodeURIComponent(token)}`,
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Link de agendamento indisponível."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicSchedulingResource>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Link de agendamento indisponível.");
  }
  return envelope.data;
}

export async function fetchPublicAvailability(
  token: string,
  from: Date,
  to: Date,
): Promise<BusySlot[]> {
  const params = new URLSearchParams({
    from: from.toISOString(),
    to: to.toISOString(),
  });
  const response = await fetch(
    `${API_BASE}/public/scheduling/resources/${encodeURIComponent(token)}/availability?${params}`,
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Não foi possível carregar a disponibilidade."));
  }
  const envelope = (await response.json()) as ApiEnvelope<{ busy: BusySlot[] }>;
  if (envelope.success === false) {
    throw new Error(envelope.message || "Não foi possível carregar a disponibilidade.");
  }
  return envelope.data?.busy ?? [];
}

export type PublicBookingPayload = {
  requester_name: string;
  requester_email: string;
  requester_phone?: string;
  title: string;
  notes?: string;
  start_at: string;
  end_at: string;
  website?: string;
};

export async function submitPublicBooking(
  token: string,
  payload: PublicBookingPayload,
): Promise<{ id: string | null; status?: string }> {
  const response = await fetch(
    `${API_BASE}/public/scheduling/resources/${encodeURIComponent(token)}/bookings`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Não foi possível enviar a solicitação."));
  }
  const envelope = (await response.json()) as ApiEnvelope<{
    id: string | null;
    status?: string;
  }>;
  if (envelope.success === false) {
    throw new Error(envelope.message || "Não foi possível enviar a solicitação.");
  }
  return {
    id: envelope.data?.id ?? null,
    status: envelope.data?.status,
  };
}
