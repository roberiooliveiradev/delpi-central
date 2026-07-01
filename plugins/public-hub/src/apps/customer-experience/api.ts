const API_BASE = "/apps/customer-experience-api";

export type PublicParticipant = {
  fullName: string;
  companyName: string;
  visitDate: string;
  participantInfo: string | null;
  thankYouMessage: string | null;
  photoUrl: string;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export async function fetchPublicParticipant(token: string): Promise<PublicParticipant | null> {
  const response = await fetch(`${API_BASE}/public/participants/${encodeURIComponent(token)}`, {
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error("Não foi possível carregar a página.");
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicParticipant>;
  if (envelope.success === false) {
    return null;
  }
  return envelope.data;
}

export function photoUrl(participant: PublicParticipant): string {
  // A API já devolve o path relativo (/apps/customer-experience-api/public/...).
  return participant.photoUrl;
}

export type FeedbackStatus = {
  fullName: string;
  submitted: boolean;
};

export async function fetchFeedbackStatus(token: string): Promise<FeedbackStatus | null> {
  const response = await fetch(
    `${API_BASE}/public/participants/${encodeURIComponent(token)}/feedback`,
    { headers: { Accept: "application/json" } },
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error("Não foi possível carregar a página.");
  }
  const envelope = (await response.json()) as ApiEnvelope<FeedbackStatus>;
  if (envelope.success === false) {
    return null;
  }
  return envelope.data;
}

export type FeedbackPayload = {
  rating: number;
  likedMost: string;
  suggestions: string;
};

export type SubmitFeedbackResult =
  | { ok: true }
  | { ok: false; status: number; message: string };

export async function submitFeedback(
  token: string,
  payload: FeedbackPayload,
): Promise<SubmitFeedbackResult> {
  const response = await fetch(
    `${API_BASE}/public/participants/${encodeURIComponent(token)}/feedback`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        rating: payload.rating,
        likedMost: payload.likedMost.trim() || null,
        suggestions: payload.suggestions.trim() || null,
      }),
    },
  );

  if (response.ok) {
    return { ok: true };
  }

  let message = "Não foi possível enviar seu feedback. Tente novamente.";
  try {
    const envelope = (await response.json()) as ApiEnvelope<unknown>;
    if (envelope?.message) {
      message = envelope.message;
    }
  } catch {
    // resposta sem corpo JSON — mantém mensagem padrão
  }
  return { ok: false, status: response.status, message };
}
