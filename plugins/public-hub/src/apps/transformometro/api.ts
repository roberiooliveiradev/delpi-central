const API_BASE = "/apps/transformometro-api";

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export type PublicSignContext = {
  outcome?: "ready" | "already_signed" | string | null;
  minute: {
    id: string;
    title?: string | null;
    minute_number?: string | null;
    meeting_date?: string | null;
    status?: string | null;
    unit_code?: string | null;
  };
  version: {
    id?: string | null;
    title?: string | null;
    agenda_html?: string;
    body_html?: string;
    decisions_html?: string;
    pending_html?: string;
    observations_html?: string;
    content_hash?: string | null;
  };
  signer: {
    id: string;
    display_name?: string | null;
    status?: string | null;
  };
  terms: string;
};

export type PublicActionResult = { ok: true } | { ok: false; status: number; message: string };

async function readErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { message?: string };
    if (body.message) return body.message;
  } catch {
    /* ignore */
  }
  return fallback;
}

export async function fetchPublicSignContext(token: string): Promise<PublicSignContext | null> {
  const response = await fetch(
    `${API_BASE}/public/meeting-minutes/sign-invites/${encodeURIComponent(token)}`,
    { headers: { Accept: "application/json" } },
  );
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Não foi possível carregar a ata."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicSignContext>;
  if (envelope.success === false) return null;
  return envelope.data;
}

export async function submitPublicSign(
  token: string,
  input: { signature: Blob; displayName: string },
): Promise<PublicActionResult> {
  const form = new FormData();
  form.append("signature", input.signature, "signature.png");
  form.append("display_name_confirmed", input.displayName);
  form.append("terms_accepted", "true");
  form.append("session_id", crypto.randomUUID());
  const response = await fetch(
    `${API_BASE}/public/meeting-minutes/sign-invites/${encodeURIComponent(token)}/sign`,
    { method: "POST", body: form, headers: { Accept: "application/json" } },
  );
  if (response.ok) return { ok: true };
  return {
    ok: false,
    status: response.status,
    message: await readErrorMessage(response, "Não foi possível registrar a assinatura."),
  };
}

export async function submitPublicRefuse(
  token: string,
  reason: string,
): Promise<PublicActionResult> {
  const response = await fetch(
    `${API_BASE}/public/meeting-minutes/sign-invites/${encodeURIComponent(token)}/refuse`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ reason }),
    },
  );
  if (response.ok) return { ok: true };
  return {
    ok: false,
    status: response.status,
    message: await readErrorMessage(response, "Não foi possível registrar a recusa."),
  };
}
