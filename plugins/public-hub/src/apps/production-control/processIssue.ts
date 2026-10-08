/**
 * Catálogo e lógica pura do «Problema de Processo» do operador (P3).
 *
 * Os códigos espelham o catálogo canônico do Requests API (P1/P2) — o backend
 * é a autoridade final da validação; aqui ficam somente label de negócio,
 * campos auxiliares e a política de Idempotency-Key da tentativa lógica.
 */

export type ProcessIssueCode =
  | "work_center_incompatible"
  | "machine_limitation"
  | "tool_not_linked"
  | "material_not_linked"
  | "process_information_missing"
  | "other";

export type ProcessIssueReason = {
  code: ProcessIssueCode;
  label: string;
  /** Campo auxiliar opcional exibido quando o motivo está selecionado. */
  auxiliaryField: "toolCode" | "materialCode" | null;
  auxiliaryLabel: string | null;
  auxiliaryPlaceholder: string | null;
};

export const PROCESS_ISSUE_REASONS: readonly ProcessIssueReason[] = [
  {
    code: "work_center_incompatible",
    label: "CT / posto não adequado",
    auxiliaryField: null,
    auxiliaryLabel: null,
    auxiliaryPlaceholder: null,
  },
  {
    code: "machine_limitation",
    label: "Limitação da máquina ou bancada",
    auxiliaryField: null,
    auxiliaryLabel: null,
    auxiliaryPlaceholder: null,
  },
  {
    code: "tool_not_linked",
    label: "Ferramenta não informada ou não vinculada",
    auxiliaryField: "toolCode",
    auxiliaryLabel: "Código da ferramenta (opcional)",
    auxiliaryPlaceholder: "Informe o código, se souber",
  },
  {
    code: "material_not_linked",
    label: "Matéria-prima não vinculada à operação",
    auxiliaryField: "materialCode",
    auxiliaryLabel: "Código do material (opcional)",
    auxiliaryPlaceholder: "Informe o código, se souber",
  },
  {
    code: "process_information_missing",
    label: "Informação de processo incompleta",
    auxiliaryField: null,
    auxiliaryLabel: null,
    auxiliaryPlaceholder: null,
  },
  {
    code: "other",
    label: "Outro problema de processo",
    auxiliaryField: null,
    auxiliaryLabel: null,
    auxiliaryPlaceholder: null,
  },
] as const;

export const PROCESS_ISSUE_TOOL_CODE_MAX_LENGTH = 60;
export const PROCESS_ISSUE_MATERIAL_CODE_MAX_LENGTH = 60;
export const PROCESS_ISSUE_NOTE_MAX_LENGTH = 500;

export const PROCESS_ISSUE_REASON_REQUIRED =
  "Selecione o tipo de problema encontrado.";

export const PROCESS_ISSUE_DISCLAIMER =
  "Esta solicitação será enviada ao departamento de Processos e não altera automaticamente a produção.";

export function processIssueReason(
  code: string | null | undefined,
): ProcessIssueReason | null {
  return (
    PROCESS_ISSUE_REASONS.find((item) => item.code === code) ?? null
  );
}

/** Rascunho informado pelo operador — identidade/contexto nunca saem daqui. */
export type ProcessIssueDraft = {
  issueCode: string;
  toolCode: string | null;
  materialCode: string | null;
  note: string | null;
};

export function isProcessIssueDraftValid(draft: ProcessIssueDraft): boolean {
  return Boolean(processIssueReason(draft.issueCode));
}

/** Assinatura estável do rascunho — base da comparação de intenção. */
export function processIssueDraftSignature(draft: ProcessIssueDraft): string {
  return JSON.stringify({
    issueCode: String(draft.issueCode ?? "").trim(),
    toolCode: String(draft.toolCode ?? "").trim(),
    materialCode: String(draft.materialCode ?? "").trim(),
    note: String(draft.note ?? "").trim(),
  });
}

/**
 * Tentativa lógica de envio (modal aberto → sucesso/cancelar).
 *
 * - `key` é a Idempotency-Key corrente, gerada na abertura do modal;
 * - `submittedSignature` registra o último payload ENVIADO — retry com o
 *   mesmo conteúdo reutiliza a chave; payload alterado = nova intenção =
 *   nova chave antes do próximo submit.
 */
export type ProcessIssueAttempt = {
  key: string;
  submittedSignature: string | null;
};

export function beginProcessIssueAttempt(
  generateKey: () => string = defaultKeyGenerator,
): ProcessIssueAttempt {
  return { key: generateKey(), submittedSignature: null };
}

export function submitKeyForDraft(
  attempt: ProcessIssueAttempt,
  draft: ProcessIssueDraft,
  generateKey: () => string = defaultKeyGenerator,
): { attempt: ProcessIssueAttempt; key: string; reused: boolean } {
  const signature = processIssueDraftSignature(draft);
  if (attempt.submittedSignature === null) {
    // Primeiro envio da tentativa — usa a chave gerada na abertura.
    return {
      attempt: { key: attempt.key, submittedSignature: signature },
      key: attempt.key,
      reused: false,
    };
  }
  if (attempt.submittedSignature === signature) {
    // Retry do mesmo envio (timeout/duplo clique) — mesma chave.
    return { attempt, key: attempt.key, reused: true };
  }
  // Payload mudou após erro: nova intenção lógica → nova chave.
  const key = generateKey();
  return {
    attempt: { key, submittedSignature: signature },
    key,
    reused: false,
  };
}

function defaultKeyGenerator(): string {
  return globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID()
    : `issue-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/** Mensagem amigável por status — nunca vaza detalhe interno/URL/token. */
export function processIssueSubmitErrorMessage(
  status: number | null,
  serverMessage?: string | null,
): string {
  if (status === 401) {
    return "Identifique-se novamente para enviar a solicitação.";
  }
  if (status === 404) {
    return "Esta operação não está mais disponível neste posto.";
  }
  if (status === 422) {
    // Rejeições do domínio chegam em PT seguro do backend.
    const message = String(serverMessage ?? "").trim();
    if (message) return message;
  }
  return "Não foi possível enviar a solicitação para Processos. Tente novamente.";
}

/** Confirmação exibida na central após o envio (sem acompanhamento — P3). */
export function processIssueConfirmationMessage(
  requestNumber: string | null | undefined,
): string {
  const number = String(requestNumber ?? "").trim();
  return number
    ? `Solicitação ${number} enviada para Processos.`
    : "Solicitação enviada para Processos.";
}
