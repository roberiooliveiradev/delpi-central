/** PRC-REF-019 — regras de apresentação do intercâmbio de informações.
 *
 * Somente montagem/validação de formulário no cliente. A validação
 * normativa (alvos, limites, duplicidade, autorização) pertence à
 * Engineering API e sempre prevalece; aqui evita-se apenas o round-trip
 * evidente. Nenhum helper decide autorização. */

import type {
  PrcFieldSpec,
  PrcInformationAnswerInput,
  PrcInformationQuestion,
  PrcInformationQuestionInput,
  PrcInformationRound,
  PrcInformationSupplierAttribute,
  PrcInformationTargetType,
} from "./api/productRegistrationApi";
import { toSupplierRows } from "./prcSuppliers";

export const INFO_QUESTION_TEXT_MAX = 1000;
export const INFO_ANSWER_TEXT_MAX = 4000;
export const INFO_MESSAGE_MAX = 1000;
export const INFO_MAX_QUESTIONS = 20;

export const INFO_TARGET_OPTIONS: ReadonlyArray<{
  value: PrcInformationTargetType;
  label: string;
}> = [
  { value: "FIELD", label: "Campo da ficha" },
  { value: "GENERAL", label: "Esclarecimento geral" },
  { value: "SUPPLIER_LINK", label: "Vínculo de fornecedor" },
];

export const INFO_SUPPLIER_ATTRIBUTE_OPTIONS: ReadonlyArray<{
  value: PrcInformationSupplierAttribute;
  label: string;
}> = [
  { value: "partNumber", label: "Part Number" },
  { value: "catalogNumber", label: "Catálogo" },
];

export type InfoQuestionDraft = {
  /** Identidade local estável da linha — nunca índice de array. */
  rowId: string;
  targetType: PrcInformationTargetType;
  targetPath: string;
  supplierCode: string;
  store: string;
  targetAttribute: PrcInformationSupplierAttribute;
  questionText: string;
};

let rowSeq = 0;

export function emptyInfoQuestion(
  targetType: PrcInformationTargetType = "GENERAL",
): InfoQuestionDraft {
  rowSeq += 1;
  return {
    rowId: `info-q-${rowSeq}`,
    targetType,
    targetPath: "",
    supplierCode: "",
    store: "",
    targetAttribute: "partNumber",
    questionText: "",
  };
}

/** Campos elegíveis como alvo FIELD: o código oficial e o agregado de
 * fornecedores têm alvo próprio (SUPPLIER_LINK / identidade do caso). */
export function questionableFieldSpecs(
  specs: PrcFieldSpec[] | null | undefined,
): PrcFieldSpec[] {
  return (specs ?? []).filter(
    (spec) => spec.path !== "officialProductCode" && spec.kind !== "suppliers",
  );
}

export type InfoSupplierOption = {
  supplierCode: string;
  store: string;
  supplierName?: string;
  /** GRANULAR-CORRECTION-09 — atributos do vínculo exibidos na tabela
   * de seleção da devolução (PN/Catálogo/fantasia atuais). */
  supplierShortName?: string;
  partNumber?: string;
  catalogNumber?: string;
};

/** Fornecedores já presentes na ficha técnica (atalho de preenchimento). */
export function supplierOptionsFromTechnicalDraft(
  technicalDraft: Record<string, unknown> | null | undefined,
): InfoSupplierOption[] {
  if (!technicalDraft) return [];
  const seen = new Set<string>();
  const out: InfoSupplierOption[] = [];
  for (const row of toSupplierRows(technicalDraft.suppliers)) {
    const code = row.supplierCode.trim();
    const store = row.store.trim();
    if (!code || !store) continue;
    const key = `${code}|${store}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      supplierCode: code,
      store,
      supplierName: row.supplierName || undefined,
      supplierShortName: row.supplierShortName || undefined,
      partNumber: row.partNumber || undefined,
      catalogNumber: row.catalogNumber || undefined,
    });
  }
  return out;
}

export function infoTargetKey(draft: InfoQuestionDraft): string | null {
  if (draft.targetType === "FIELD") {
    return draft.targetPath ? `FIELD:${draft.targetPath}` : null;
  }
  if (draft.targetType === "SUPPLIER_LINK") {
    return `SUPPLIER:${draft.supplierCode.trim()}|${draft.store.trim()}|${draft.targetAttribute}`;
  }
  return null; // GENERAL pode repetir
}

export type InfoQuestionsValidation = {
  valid: boolean;
  /** Erro por `rowId`. */
  rowErrors: Record<string, string>;
  formError: string;
};

export function validateInfoQuestions(
  drafts: InfoQuestionDraft[],
): InfoQuestionsValidation {
  const rowErrors: Record<string, string> = {};
  if (!drafts.length) {
    return {
      valid: false,
      rowErrors,
      formError: "Informe ao menos uma pergunta.",
    };
  }
  if (drafts.length > INFO_MAX_QUESTIONS) {
    return {
      valid: false,
      rowErrors,
      formError: `Máximo de ${INFO_MAX_QUESTIONS} perguntas por solicitação.`,
    };
  }
  const seen = new Set<string>();
  for (const draft of drafts) {
    const text = draft.questionText.trim();
    if (!text) {
      rowErrors[draft.rowId] = "Escreva a pergunta.";
      continue;
    }
    if (text.length > INFO_QUESTION_TEXT_MAX) {
      rowErrors[draft.rowId] =
        `A pergunta excede ${INFO_QUESTION_TEXT_MAX} caracteres.`;
      continue;
    }
    if (draft.targetType === "FIELD" && !draft.targetPath) {
      rowErrors[draft.rowId] = "Selecione o campo da ficha.";
      continue;
    }
    if (
      draft.targetType === "SUPPLIER_LINK" &&
      (!draft.supplierCode.trim() || !draft.store.trim())
    ) {
      rowErrors[draft.rowId] = "Informe o código e a loja do fornecedor.";
      continue;
    }
    const key = infoTargetKey(draft);
    if (key) {
      if (seen.has(key)) {
        rowErrors[draft.rowId] =
          "Este alvo já possui uma pergunta nesta solicitação.";
        continue;
      }
      seen.add(key);
    }
  }
  const valid = Object.keys(rowErrors).length === 0;
  return {
    valid,
    rowErrors,
    formError: valid ? "" : "Revise as perguntas destacadas.",
  };
}

export function buildQuestionInputs(
  drafts: InfoQuestionDraft[],
): PrcInformationQuestionInput[] {
  return drafts.map((draft) => {
    const questionText = draft.questionText.trim();
    if (draft.targetType === "FIELD") {
      return { targetType: "FIELD", targetPath: draft.targetPath, questionText };
    }
    if (draft.targetType === "SUPPLIER_LINK") {
      return {
        targetType: "SUPPLIER_LINK",
        targetAttribute: draft.targetAttribute,
        supplierKey: {
          supplierCode: draft.supplierCode.trim(),
          store: draft.store.trim(),
        },
        questionText,
      };
    }
    return { targetType: "GENERAL", questionText };
  });
}

/** Paths FIELD distintos (compatibilidade com o campo legado). */
export function pendingFieldsFromDrafts(drafts: InfoQuestionDraft[]): string[] {
  const out: string[] = [];
  for (const draft of drafts) {
    if (
      draft.targetType === "FIELD" &&
      draft.targetPath &&
      !out.includes(draft.targetPath)
    ) {
      out.push(draft.targetPath);
    }
  }
  return out;
}

/** Re-pergunta (complemento) sobre o mesmo alvo da pergunta original. */
export function followUpInputFor(
  question: PrcInformationQuestion,
  questionText: string,
): PrcInformationQuestionInput {
  const text = questionText.trim();
  if (question.targetType === "FIELD") {
    return {
      targetType: "FIELD",
      targetPath: question.targetPath ?? null,
      questionText: text,
    };
  }
  if (question.targetType === "SUPPLIER_LINK") {
    return {
      targetType: "SUPPLIER_LINK",
      targetAttribute: question.targetAttribute ?? null,
      supplierKey: question.supplierKey ?? null,
      questionText: text,
    };
  }
  return { targetType: "GENERAL", questionText: text };
}

/** Rodada ativa = a que ainda bloqueia o atendimento. */
export function findActiveInformationRound(
  rounds: PrcInformationRound[],
): PrcInformationRound | null {
  const active = rounds.filter((r) => r.status !== "resolved");
  if (!active.length) return null;
  return [...active].sort(
    (a, b) => (b.sequence ?? 0) - (a.sequence ?? 0),
  )[0];
}

export function resolvedInformationRounds(
  rounds: PrcInformationRound[],
): PrcInformationRound[] {
  return rounds
    .filter((r) => r.status === "resolved")
    .sort((a, b) => (b.sequence ?? 0) - (a.sequence ?? 0));
}

export function allInformationQuestionsAccepted(
  questions: PrcInformationQuestion[],
): boolean {
  return (
    questions.length > 0 && questions.every((q) => q.status === "accepted")
  );
}

export type InfoAnswerValidation = {
  valid: boolean;
  /** Erro por `questionId`. */
  errors: Record<string, string>;
};

/** Envio exige resposta não vazia em todas as perguntas da rodada. */
export function validateInfoAnswersForSubmit(
  questions: PrcInformationQuestion[],
  texts: Record<string, string>,
): InfoAnswerValidation {
  const errors: Record<string, string> = {};
  for (const q of questions) {
    const text = (texts[q.id] ?? "").trim();
    if (!text) errors[q.id] = "Responda esta pergunta para enviar.";
    else if (text.length > INFO_ANSWER_TEXT_MAX) {
      errors[q.id] = `A resposta excede ${INFO_ANSWER_TEXT_MAX} caracteres.`;
    }
  }
  return { valid: Object.keys(errors).length === 0, errors };
}

export function buildAnswerInputs(
  questions: PrcInformationQuestion[],
  texts: Record<string, string>,
): PrcInformationAnswerInput[] {
  return questions.map((q) => ({
    questionId: q.id,
    text: (texts[q.id] ?? "").trim(),
  }));
}

export function initialAnswerTexts(
  questions: PrcInformationQuestion[],
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const q of questions) out[q.id] = q.answer?.text ?? "";
  return out;
}

/** Identidade conhecida e match de solicitante — fail-closed se ausente. */
export function isRequesterSubject(
  currentSubject: string | null | undefined,
  requesterSubject: string | null | undefined,
): boolean {
  const current = (currentSubject || "").trim();
  const requester = (requesterSubject || "").trim();
  if (!current || !requester) return false;
  return current === requester;
}

/**
 * Apresentação contínua do painel (FIX-02) — estado da rodada + capacidades.
 * Não é autorização; só decide o que renderizar.
 */
export type InfoPresentation =
  | "loading"
  | "error"
  | "empty"
  | "awaiting_requester_form"
  | "awaiting_requester_watch"
  | "awaiting_review_analyst"
  | "awaiting_review_watch"
  | "resolved_ready"
  | "resolved_done";

export function resolveInfoPresentation(input: {
  loadState: "loading" | "ok" | "error";
  hasRounds: boolean;
  activeStatus: string | null | undefined;
  canRespond: boolean;
  canReview: boolean;
  canResume: boolean;
}): InfoPresentation {
  if (input.loadState === "loading" && !input.hasRounds) return "loading";
  if (input.loadState === "error" && !input.hasRounds) return "error";
  if (!input.activeStatus) {
    if (!input.hasRounds) return "empty";
    return input.canResume ? "resolved_ready" : "resolved_done";
  }
  if (input.activeStatus === "awaiting_requester") {
    return input.canRespond
      ? "awaiting_requester_form"
      : "awaiting_requester_watch";
  }
  if (input.activeStatus === "awaiting_review") {
    return input.canReview
      ? "awaiting_review_analyst"
      : "awaiting_review_watch";
  }
  return input.canResume ? "resolved_ready" : "resolved_done";
}

/** Mensagem funcional para 409 de rodada aberta (sem código técnico na UI). */
export function informationRoundConflictMessage(
  rawMessage: string | undefined,
  fallback: string,
): string {
  const text = String(rawMessage || "");
  if (/information_round_open/i.test(text)) return fallback;
  return text.trim() || fallback;
}
