import type {
  ComparisonState,
  DecisionState,
  EligibilityState,
  EnrichmentReviewStatus,
} from "./types";

export const ENRICHMENT_CONTENT = {
  sectionTitle: "Enriquecimento cadastral",
  sectionHint:
    "Compara o cadastro do Protheus com dados públicos de pessoa jurídica da BrasilAPI. " +
    "A fonte externa é apenas sugestão — nenhuma alteração é gravada no ERP por esta tela.",
  sourceNote:
    "Fonte externa de dados públicos (terceiros). Não é base oficial da Receita nem autoridade de homologação.",

  consultAction: "Consultar dados externos",
  consultLoading: "Consultando a fonte externa…",
  newConsultAction: "Nova consulta",

  emptyTitle: "Nenhuma consulta realizada",
  emptyMessage:
    "Compare o cadastro com dados públicos do CNPJ para receber sugestões de atualização por campo.",

  comparisonTitle: "Comparação de campos",
  comparisonHint:
    "Para cada campo: valor atual no Protheus, valor sugerido pela fonte externa e situação da comparação. Aceitar só é permitido em campos elegíveis.",
  columnField: "Campo",
  columnCurrent: "Atual (Protheus)",
  columnSuggested: "Sugerido (fonte externa)",
  columnStatus: "Situação",
  columnDecision: "Decisão",
  selectLabel: "Selecionar",
  sourceNotProvided: "Fonte não fornece",
  currentNotProvided: "Não informado",
  protectedValue: "Protegido",

  acceptAction: "Aceitar",
  rejectAction: "Rejeitar",
  decidingLabel: "Registrando…",
  replayNotice: "Esta decisão já estava registrada — nenhuma duplicação foi aplicada.",

  bulkBarLabel: "Decisões em lote",
  bulkAccept: "Aceitar selecionados",
  bulkReject: "Rejeitar selecionados",
  bulkAcceptBlocked: "O aceite em lote exige que todos os campos selecionados sejam elegíveis.",
  bulkConfirmTitle: "Confirmar decisão em lote",
  bulkConfirmAccept: (count: number) =>
    `Confirmar aceite de ${count} campo(s) elegível(is)?`,
  bulkConfirmReject: (count: number) =>
    `Confirmar rejeição de ${count} campo(s)?`,
  bulkConfirmAction: "Confirmar",
  bulkCancelAction: "Voltar",

  summary: (different: number, match: number, other: number) =>
    `${different} divergência(s) · ${match} igual(is) · ${other} sem sugestão aplicável`,
  acceptedSummary: (accepted: number, rejected: number, pending: number) =>
    `Aceitos: ${accepted} · Rejeitados: ${rejected} · Pendentes: ${pending}`,

  prepareAction: "Preparar atualização",
  prepareHint:
    "Consolida os campos aceitos em um rascunho de atualização. Nenhum dado é gravado no Protheus.",
  draftTitle: "Rascunho de atualização",
  draftReady:
    "Rascunho preparado. Nenhum dado foi gravado no Protheus.",
  draftEmpty: "Nenhum campo aceito — não há rascunho de atualização.",
  draftBaseline: (status: string) => `Baseline: ${status} · escrita ERP desabilitada`,
  draftColumnCurrent: "Atual",
  draftColumnProposed: "Rascunho",

  historyTitle: "Revisões anteriores",
  historyHint: "Consultas feitas por você para este fornecedor.",
  historyLoading: "Carregando histórico…",
  historyEmpty: "Nenhuma revisão registrada para este fornecedor.",
  historyPartial:
    "Histórico indisponível no momento; a revisão atual continua utilizável.",
  columnReviewedAt: "Consulta",
  columnSource: "Fonte",
  columnReviewStatus: "Status",
  columnRevision: "Rev.",
  columnExpires: "Expira",
  openReviewAction: "Abrir",

  errorGeneric:
    "Não foi possível concluir a operação de enriquecimento. Tente novamente ou fale com o suporte.",
  errorForbidden: "Você não tem acesso a esta revisão de enriquecimento.",
  errorNotFound: "Revisão não encontrada.",
  errorRateLimited:
    "Limite de consultas atingido. Aguarde alguns segundos e tente novamente.",
  errorSourceUnavailable:
    "A fonte externa está temporariamente indisponível. Tente novamente em instantes.",
  errorInvalidResponse:
    "A fonte externa retornou uma resposta inválida. Nenhuma comparação foi aplicada.",
  errorTaxIdNotFound: "CNPJ não localizado na fonte externa.",
  errorInvalidTaxId: "O documento do fornecedor não é um CNPJ válido para consulta.",
  errorUnsupportedDocument:
    "O enriquecimento externo é disponível apenas para pessoa jurídica (CNPJ).",
  errorReviewExpired:
    "Esta revisão expirou. Inicie uma nova consulta para comparar dados atualizados.",
  errorStaleBaseline:
    "O cadastro do fornecedor mudou desde a consulta. Recarregue a ficha e revise novamente.",
  errorRevisionConflict:
    "A revisão foi atualizada em outra ação. Os dados foram recarregados.",
  errorIdempotencyConflict:
    "Operação já registrada com dados diferentes. Nenhuma duplicação foi aplicada.",
  errorAlreadyDecided: "Este campo já possui decisão registrada.",
  errorNotEligible: "Este campo não é elegível para aceite.",
  errorCancelled: "Esta revisão foi cancelada.",

  retryAction: "Tentar novamente",
} as const;

export const COMPARISON_LABELS: Record<ComparisonState, string> = {
  MATCH: "Igual",
  DIFFERENT: "Divergente",
  SOURCE_MISSING: "Sem fonte",
  CURRENT_MISSING: "Sem valor atual",
  NOT_COMPARABLE: "Não comparável",
  PROTECTED: "Protegido",
  UNSUPPORTED: "Não suportado",
  ERROR: "Erro",
};

export const COMPARISON_VARIANTS: Record<
  ComparisonState,
  "neutral" | "info" | "success" | "warning" | "danger"
> = {
  MATCH: "success",
  DIFFERENT: "warning",
  SOURCE_MISSING: "neutral",
  CURRENT_MISSING: "info",
  NOT_COMPARABLE: "neutral",
  PROTECTED: "neutral",
  UNSUPPORTED: "neutral",
  ERROR: "danger",
};

export const ELIGIBILITY_LABELS: Record<EligibilityState, string> = {
  ELIGIBLE_TO_APPLY: "Elegível",
  PROTECTED: "Protegido",
  NOT_APPLICABLE: "Não aplicável",
  PENDING_VALIDATION: "Pendente de validação",
};

export const DECISION_LABELS: Record<DecisionState, string> = {
  PENDING: "Pendente",
  ACCEPTED_FOR_DRAFT: "Aceito",
  REJECTED_SUGGESTION: "Rejeitado",
};

export const REVIEW_STATUS_LABELS: Record<EnrichmentReviewStatus, string> = {
  IN_REVIEW: "Em revisão",
  DECIDED: "Decidida",
  EXPIRED: "Expirada",
  STALE: "Desatualizada",
  CANCELLED: "Cancelada",
};

/** Mapeia `ApiRequestError` real do BFF para mensagem útil PT-BR. */
export function mapEnrichmentError(status?: number, code?: string): string {
  switch (code) {
    case "ENRICHMENT_UNSUPPORTED_DOCUMENT":
      return ENRICHMENT_CONTENT.errorUnsupportedDocument;
    case "ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND":
      return ENRICHMENT_CONTENT.errorTaxIdNotFound;
    case "ENRICHMENT_REGISTRY_INVALID_TAX_ID":
      return ENRICHMENT_CONTENT.errorInvalidTaxId;
    case "ENRICHMENT_REGISTRY_INVALID_RESPONSE":
      return ENRICHMENT_CONTENT.errorInvalidResponse;
    case "ENRICHMENT_SOURCE_UNAVAILABLE":
    case "ENRICHMENT_RATE_LIMITER_UNAVAILABLE":
      return ENRICHMENT_CONTENT.errorSourceUnavailable;
    case "ENRICHMENT_RATE_LIMITED":
      return ENRICHMENT_CONTENT.errorRateLimited;
    case "ENRICHMENT_REVIEW_EXPIRED":
      return ENRICHMENT_CONTENT.errorReviewExpired;
    case "ENRICHMENT_STALE_BASELINE":
      return ENRICHMENT_CONTENT.errorStaleBaseline;
    case "ENRICHMENT_REVISION_CONFLICT":
      return ENRICHMENT_CONTENT.errorRevisionConflict;
    case "ENRICHMENT_IDEMPOTENCY_CONFLICT":
      return ENRICHMENT_CONTENT.errorIdempotencyConflict;
    case "ENRICHMENT_PROPOSAL_ALREADY_DECIDED":
      return ENRICHMENT_CONTENT.errorAlreadyDecided;
    case "ENRICHMENT_PROPOSAL_NOT_ELIGIBLE":
      return ENRICHMENT_CONTENT.errorNotEligible;
    case "ENRICHMENT_REVIEW_CANCELLED":
      return ENRICHMENT_CONTENT.errorCancelled;
    case "forbidden":
      return ENRICHMENT_CONTENT.errorForbidden;
    case "not_found":
      return ENRICHMENT_CONTENT.errorNotFound;
    default:
      break;
  }
  if (status === 403) return ENRICHMENT_CONTENT.errorForbidden;
  if (status === 404) return ENRICHMENT_CONTENT.errorNotFound;
  if (status === 429) return ENRICHMENT_CONTENT.errorRateLimited;
  if (status === 503) return ENRICHMENT_CONTENT.errorSourceUnavailable;
  return ENRICHMENT_CONTENT.errorGeneric;
}
