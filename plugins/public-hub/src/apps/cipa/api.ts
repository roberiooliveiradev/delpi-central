const API_BASE = "/apps/cipa-api";

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export type SipatQuestionType =
  | "single_choice"
  | "multi_choice"
  | "likert_5"
  | "yes_no"
  | "text_short"
  | "text_long";

export type PublicSipatQuestion = {
  id: string;
  position?: number;
  type: SipatQuestionType;
  label: string;
  helpText?: string | null;
  required: boolean;
  options?: string[] | null;
};

export type PublicSipatSurvey = {
  id: string;
  title: string;
  description?: string | null;
  unit_code: string;
  questions: PublicSipatQuestion[];
};

export type SipatAnswerPayload = {
  question_id: string;
  value?: string | null;
  choices?: string[];
};

export async function fetchPublicSipatSurvey(token: string): Promise<PublicSipatSurvey | null> {
  const response = await fetch(`${API_BASE}/public/sipat/${encodeURIComponent(token)}`, {
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    let message = "Não foi possível carregar a pesquisa.";
    try {
      const body = (await response.json()) as { message?: string };
      if (body.message) message = body.message;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicSipatSurvey>;
  if (envelope.success === false) {
    return null;
  }
  return envelope.data;
}

export type SubmitSipatResult =
  | { ok: true }
  | { ok: false; status: number; message: string };

export async function submitPublicSipatResponse(
  token: string,
  answers: SipatAnswerPayload[],
): Promise<SubmitSipatResult> {
  const response = await fetch(
    `${API_BASE}/public/sipat/${encodeURIComponent(token)}/responses`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ answers }),
    },
  );

  if (response.ok) {
    return { ok: true };
  }

  let message = "Não foi possível enviar suas respostas. Tente novamente.";
  try {
    const envelope = (await response.json()) as ApiEnvelope<unknown>;
    if (envelope?.message) {
      message = envelope.message;
    }
  } catch {
    /* ignore */
  }
  return { ok: false, status: response.status, message };
}
