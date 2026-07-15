const API_BASE = "/apps/api-delpi";

export type PublicKaizenSuggestionPayload = {
  proposer_name: string;
  sector: string;
  employee_registration: string;
  work_center_or_location: string;
  problem_description: string;
  proposed_solution: string;
  branch_code?: "01" | "02";
  website?: string;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export async function submitPublicKaizenSuggestion(
  payload: PublicKaizenSuggestionPayload,
): Promise<{ id: string | null }> {
  const response = await fetch(`${API_BASE}/public/kaizen/suggestions`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let message = "Não foi possível enviar a sugestão.";
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
    throw new Error(envelope.message || "Não foi possível enviar a sugestão.");
  }
  return { id: envelope.data?.id ?? null };
}
