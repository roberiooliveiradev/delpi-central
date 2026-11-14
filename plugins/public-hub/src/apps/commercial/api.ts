/**
 * Cliente HTTP da Pesquisa de Satisfação pública (commercial-api).
 * Sem bearer, sem cookies e sem referrer: o token do convite nunca é enviado a terceiros.
 * A API é a autoridade de janela, unicidade e validação final.
 */
const API_BASE = "/apps/commercial-api";
const PUBLIC_PATH = "/public/satisfaction-surveys";
const REQUEST_TIMEOUT_MS = 20_000;

export type SurveyItemKind = "dimension" | "overall" | "recommendation" | "open";

export type SurveyQuestionItem = {
  order: number;
  key: string;
  title: string;
  prompt: string;
  kind: SurveyItemKind;
  allowsNotApplicable: boolean;
  required: boolean;
  scaleMin: number | null;
  scaleMax: number | null;
};

export type SurveyQuestionnaire = {
  version: string;
  scaleLabels: Record<number, string>;
  items: SurveyQuestionItem[];
};

export type SurveyWindow = {
  campaignName: string;
  startsAt: string;
  endsAt: string;
};

/** Estado do link devolvido pela API (ou derivado de falha segura). */
export type PublicSurveyState =
  | ({
      status: "open";
      questionnaire: SurveyQuestionnaire;
      token: string;
      companyName: string | null;
    } & SurveyWindow)
  | ({ status: "not_open" | "closed" | "already_submitted" } & SurveyWindow)
  | { status: "invalid" }
  | { status: "temporary_error" };

export type SurveyAnswerPayload = {
  overall_score: number;
  recommendation_score: number;
  dimensions: Record<string, number | null>;
  strengths: string | null;
  improvements: string | null;
  unmet_needs: string | null;
};

export type SubmitOutcome =
  | { outcome: "submitted" }
  | {
      outcome: "already_submitted" | "not_open" | "closed" | "invalid" | "temporary_error" | "rejected";
      message: string;
    };

type Envelope = {
  success?: boolean;
  message?: string;
  data?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

const KINDS: readonly SurveyItemKind[] = ["dimension", "overall", "recommendation", "open"];

/**
 * Valida o catálogo recebido: a página só renderiza o questionário oficial completo
 * (10 dimensões + satisfação geral + recomendação + 3 abertas). Qualquer desvio é tratado
 * como indisponibilidade, nunca como formulário parcial.
 */
export function normalizeQuestionnaire(raw: unknown): SurveyQuestionnaire | null {
  if (!isRecord(raw) || !Array.isArray(raw.items)) return null;
  const items: SurveyQuestionItem[] = [];
  for (const entry of raw.items) {
    if (!isRecord(entry)) return null;
    const kind = entry.kind;
    if (typeof kind !== "string" || !(KINDS as readonly string[]).includes(kind)) return null;
    const order = num(entry.order);
    const key = str(entry.key);
    const prompt = str(entry.prompt);
    if (order === null || !key || !prompt) return null;
    items.push({
      order,
      key,
      title: str(entry.title, key),
      prompt,
      kind: kind as SurveyItemKind,
      allowsNotApplicable: entry.allows_not_applicable === true,
      required: entry.required === true,
      scaleMin: num(entry.scale_min),
      scaleMax: num(entry.scale_max),
    });
  }
  items.sort((a, b) => a.order - b.order);
  const count = (kind: SurveyItemKind) => items.filter((item) => item.kind === kind).length;
  if (
    items.length !== 15 ||
    count("dimension") !== 10 ||
    count("overall") !== 1 ||
    count("recommendation") !== 1 ||
    count("open") !== 3
  ) {
    return null;
  }
  const scaleLabels: Record<number, string> = {};
  if (isRecord(raw.scale_1_5_labels)) {
    for (const [scale, label] of Object.entries(raw.scale_1_5_labels)) {
      const value = Number(scale);
      if (Number.isInteger(value) && typeof label === "string") scaleLabels[value] = label;
    }
  }
  return { version: str(raw.questionnaire_version), scaleLabels, items };
}

function surveyUrl(token: string, suffix = ""): string {
  return `${API_BASE}${PUBLIC_PATH}/${encodeURIComponent(token)}${suffix}`;
}

function errorCode(body: unknown): string | null {
  if (!isRecord(body) || !isRecord(body.data)) return null;
  return typeof body.data.code === "string" ? body.data.code : null;
}

async function readEnvelope(response: Response): Promise<Envelope | null> {
  try {
    const parsed: unknown = await response.json();
    return isRecord(parsed) ? (parsed as Envelope) : null;
  } catch {
    return null;
  }
}

async function request(url: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, {
      ...init,
      credentials: "omit",
      referrerPolicy: "no-referrer",
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

/** Interpreta o corpo `200` do GET público em um estado de UI. */
export function parsePublicSurvey(token: string, data: unknown): PublicSurveyState {
  if (!isRecord(data)) return { status: "temporary_error" };
  const window: SurveyWindow = {
    campaignName: str(data.campaign_name),
    startsAt: str(data.starts_at),
    endsAt: str(data.ends_at),
  };
  const status = data.status;
  if (status === "not_open" || status === "closed" || status === "already_submitted") {
    return { status, ...window };
  }
  if (status === "open") {
    const questionnaire = normalizeQuestionnaire(data.questionnaire);
    if (!questionnaire) return { status: "temporary_error" };
    return {
      status: "open",
      token,
      questionnaire,
      companyName: str(data.company_name) || null,
      ...window,
    };
  }
  return { status: "temporary_error" };
}

export async function fetchPublicSurvey(token: string): Promise<PublicSurveyState> {
  let response: Response;
  try {
    response = await request(surveyUrl(token), {
      method: "GET",
      headers: { Accept: "application/json" },
    });
  } catch {
    return { status: "temporary_error" };
  }
  const body = await readEnvelope(response);
  if (response.ok && body?.success !== false) {
    return parsePublicSurvey(token, body?.data);
  }
  if (response.status === 404 || errorCode(body) === "invalid_token") {
    return { status: "invalid" };
  }
  return { status: "temporary_error" };
}

const DEFAULT_SUBMIT_ERROR = "Não foi possível confirmar o envio. Tente novamente.";

/** Traduz falha do POST em desfecho seguro (nunca confirma sucesso sem `2xx`). */
export function classifySubmitFailure(status: number, body: Envelope | null): SubmitOutcome {
  const message = typeof body?.message === "string" && body.message ? body.message : DEFAULT_SUBMIT_ERROR;
  const code = errorCode(body);
  if (code === "already_submitted") return { outcome: "already_submitted", message };
  if (code === "not_open") return { outcome: "not_open", message };
  if (code === "closed") return { outcome: "closed", message };
  if (code === "invalid_token" || status === 404) return { outcome: "invalid", message };
  if (status === 400 || status === 422) return { outcome: "rejected", message };
  return { outcome: "temporary_error", message: status >= 500 ? DEFAULT_SUBMIT_ERROR : message };
}

export async function submitPublicSurvey(
  token: string,
  payload: SurveyAnswerPayload,
): Promise<SubmitOutcome> {
  let response: Response;
  try {
    response = await request(surveyUrl(token, "/response"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    // Timeout/rede: o servidor pode ou não ter gravado. Nunca afirmar sucesso nem reenviar sozinho.
    return { outcome: "temporary_error", message: DEFAULT_SUBMIT_ERROR };
  }
  if (response.ok) return { outcome: "submitted" };
  return classifySubmitFailure(response.status, await readEnvelope(response));
}
