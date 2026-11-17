/** Routing Study Workspace V2 — rascunho de sessão (contrato
 * `routing-study-session-state-contract.md`).
 *
 * Persistência best-effort em `sessionStorage`, isolada por
 * identidade (sub do JWT — chave não sensível), produto, filial,
 * estágio e versão do schema. Nunca armazena tokens, PII, payloads
 * oficiais completos ou resultados — resultados calculados são
 * transitórios e precisam ser recalculados após refresh (ST-05/06).
 *
 * Este módulo é puro: recebe um Storage injetado para ser testável
 * sem DOM. A montagem da chave nunca usa `branch=all` como filial
 * física — preserva a seleção explícita ("all" é rótulo de escopo). */

import type { RoutingStageView } from "./routingGrouping";

export const STUDY_SCHEMA_VERSION = 2;
export const STUDY_STORAGE_PREFIX = "engineering:routing-study";
export const STUDY_MAX_SCENARIOS = 4;
export const STUDY_MAX_POSTS = 12;

export type StudyMode = "quick" | "posts";

/** Inputs do formulário preservados como texto — o usuário pode
 * digitar valores intermediários ("1.5" em andamento) que não são
 * números válidos ainda; serializar como string não perde edição. */
export type StudyInputs = {
  demand: string;
  shiftMinutes: string;
  breakMinutes: string;
  batchSize: string;
  numStations: string;
};

export type HypotheticalPost = {
  /** ID local estável — nunca confundir com código oficial. */
  clientId: string;
  name: string;
  /** Referências `RoutingOperationView.key` — somente operações
   * oficiais existentes podem ser vinculadas. */
  operationRefs: string[];
  operators: number | null;
  parallelPositions: number | null;
  note: string;
};

export type StudyScenarioDraft = {
  clientId: string;
  /** Letra exibida — "A", "B", "C"… (UI prefixa "Cenário"). */
  label: string;
  mode: StudyMode;
  inputs: StudyInputs;
  posts: HypotheticalPost[];
};

export type StudyDraftContext = {
  productCode: string;
  branch: string;
  stageKey: string;
  sourceFingerprint: string;
};

export type RoutingStudyDraft = {
  schemaVersion: typeof STUDY_SCHEMA_VERSION;
  savedAt: string;
  context: StudyDraftContext;
  activeScenarioId: string;
  scenarios: StudyScenarioDraft[];
};

/* --- chave ------------------------------------------------------------ */

/** `sub` do JWT (UUID opaco) ou "anonymous" quando a sessão ainda não
 * expôs identidade — nunca JWT/email completos na chave. */
export function buildStorageKey(
  identity: string | null,
  context: StudyDraftContext,
): string {
  const who = identity?.trim() || "anonymous";
  const branch = context.branch.trim() || "all";
  return [
    STUDY_STORAGE_PREFIX,
    `v${STUDY_SCHEMA_VERSION}`,
    who,
    context.productCode,
    branch,
    context.stageKey,
  ].join(":");
}

/* --- fingerprint da fonte ---------------------------------------------- */

/** Hash estável (FNV-1a 32 bits) da identidade oficial das operações —
 * detecta roteiro alterado sem guardar payload oficial. */
export function computeSourceFingerprint(stage: RoutingStageView): string {
  let hash = 0x811c9dc5;
  const feed = (s: string) => {
    for (let i = 0; i < s.length; i++) {
      hash ^= s.charCodeAt(i);
      hash = Math.imul(hash, 0x01000193);
    }
  };
  feed(stage.key);
  for (const op of stage.operations) {
    feed(
      `${op.key}|${op.operation_code}|${op.work_center ?? ""}|` +
        `${op.resource_code ?? ""}|${op.time_minutes_piece ?? ""}`,
    );
  }
  return (hash >>> 0).toString(16);
}

/* --- fingerprint dos parâmetros (staleness de resultado) ---------------- */

/** Identidade dos parâmetros PROVIDed que entraram no cálculo — se os
 * inputs mudarem depois de um resultado, o resultado vira STALE. */
export function inputsFingerprint(inputs: {
  demand?: number;
  available_minutes?: number;
  num_stations?: number;
  batch_size?: number;
  branch?: string;
}): string {
  return [
    inputs.demand ?? "",
    inputs.available_minutes ?? "",
    inputs.num_stations ?? "",
    inputs.batch_size ?? "",
    inputs.branch ?? "",
  ].join("|");
}

/* --- fábricas ----------------------------------------------------------- */

export const SCENARIO_LABELS = ["A", "B", "C", "D"] as const;

export function emptyInputs(): StudyInputs {
  return {
    demand: "",
    shiftMinutes: "",
    breakMinutes: "",
    batchSize: "",
    numStations: "",
  };
}

let clientSeq = 0;
export function newClientId(prefix: string): string {
  clientSeq += 1;
  return `${prefix}-${Date.now().toString(36)}-${clientSeq}`;
}

export function newScenarioDraft(label: string): StudyScenarioDraft {
  return {
    clientId: newClientId("scenario"),
    label,
    mode: "quick",
    inputs: emptyInputs(),
    posts: [],
  };
}

export function emptyDraft(context: StudyDraftContext): RoutingStudyDraft {
  const first = newScenarioDraft(SCENARIO_LABELS[0]);
  return {
    schemaVersion: STUDY_SCHEMA_VERSION,
    savedAt: new Date().toISOString(),
    context,
    activeScenarioId: first.clientId,
    scenarios: [first],
  };
}

/* --- validação / parse --------------------------------------------------- */

export type DraftParseResult =
  | { ok: true; draft: RoutingStudyDraft }
  | { ok: false; reason: "invalid_json" | "invalid_schema" | "wrong_context" | "wrong_version" };

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function validPost(v: unknown): v is HypotheticalPost {
  return (
    isRecord(v) &&
    typeof v.clientId === "string" &&
    typeof v.name === "string" &&
    Array.isArray(v.operationRefs) &&
    v.operationRefs.every((r) => typeof r === "string") &&
    (v.operators === null || typeof v.operators === "number") &&
    (v.parallelPositions === null ||
      typeof v.parallelPositions === "number") &&
    typeof v.note === "string"
  );
}

function validInputs(v: unknown): v is StudyInputs {
  return (
    isRecord(v) &&
    typeof v.demand === "string" &&
    typeof v.shiftMinutes === "string" &&
    typeof v.breakMinutes === "string" &&
    typeof v.batchSize === "string" &&
    typeof v.numStations === "string"
  );
}

function validScenario(v: unknown): v is StudyScenarioDraft {
  return (
    isRecord(v) &&
    typeof v.clientId === "string" &&
    typeof v.label === "string" &&
    (v.mode === "quick" || v.mode === "posts") &&
    validInputs(v.inputs) &&
    Array.isArray(v.posts) &&
    v.posts.length <= STUDY_MAX_POSTS &&
    v.posts.every(validPost)
  );
}

/** Parse defensivo — storage é untrusted: pode conter JSON inválido,
 * schema de versão anterior ou rascunho de outro contexto. */
export function parseDraft(
  raw: string | null,
  context: StudyDraftContext,
): DraftParseResult {
  if (!raw) return { ok: false, reason: "invalid_json" };
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    return { ok: false, reason: "invalid_json" };
  }
  if (!isRecord(data)) return { ok: false, reason: "invalid_schema" };
  if (data.schemaVersion !== STUDY_SCHEMA_VERSION) {
    return { ok: false, reason: "wrong_version" };
  }
  const ctx = data.context;
  if (
    !isRecord(ctx) ||
    ctx.productCode !== context.productCode ||
    (ctx.branch ?? "") !== context.branch ||
    ctx.stageKey !== context.stageKey ||
    typeof ctx.sourceFingerprint !== "string"
  ) {
    return { ok: false, reason: "wrong_context" };
  }
  if (
    !Array.isArray(data.scenarios) ||
    !data.scenarios.length ||
    data.scenarios.length > STUDY_MAX_SCENARIOS ||
    !data.scenarios.every(validScenario) ||
    typeof data.activeScenarioId !== "string" ||
    !data.scenarios.some(
      (s) => (s as StudyScenarioDraft).clientId === data.activeScenarioId,
    )
  ) {
    return { ok: false, reason: "invalid_schema" };
  }
  return {
    ok: true,
    draft: {
      schemaVersion: STUDY_SCHEMA_VERSION,
      savedAt: typeof data.savedAt === "string" ? data.savedAt : "",
      context: {
        productCode: String(ctx.productCode),
        branch: String(ctx.branch ?? ""),
        stageKey: String(ctx.stageKey),
        sourceFingerprint: String(ctx.sourceFingerprint),
      },
      activeScenarioId: String(data.activeScenarioId),
      scenarios: data.scenarios as StudyScenarioDraft[],
    },
  };
}

/* --- storage ------------------------------------------------------------ */

export type DraftSaveOutcome = "saved" | "unavailable" | "quota" | "error";

export function saveDraft(
  storage: Storage | null,
  key: string,
  draft: RoutingStudyDraft,
): DraftSaveOutcome {
  if (!storage) return "unavailable";
  try {
    storage.setItem(key, JSON.stringify(draft));
    return "saved";
  } catch (e) {
    if (e instanceof DOMException && e.name === "QuotaExceededError") {
      return "quota";
    }
    return "error";
  }
}

export function loadDraft(
  storage: Storage | null,
  key: string,
): string | null {
  if (!storage) return null;
  try {
    return storage.getItem(key);
  } catch {
    return null;
  }
}

export function removeDraft(storage: Storage | null, key: string): boolean {
  if (!storage) return false;
  try {
    storage.removeItem(key);
    return storage.getItem(key) === null;
  } catch {
    return false;
  }
}
