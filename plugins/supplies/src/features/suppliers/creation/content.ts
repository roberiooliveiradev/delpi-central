/** Copy PT-BR do cadastro assistido + mapa de erros da prévia (X4.UX-R1.S2). */

import { ApiRequestError } from "../../../api/httpClient";

export const CREATION_CONTENT = {
  modeSelectorTitle: "Como você quer começar?",
  modeCnpjLabel: "Consultar por CNPJ",
  modeCnpjHint:
    "Informe o CNPJ para buscar dados cadastrais públicos e revisar sugestões de preenchimento.",
  modeNameLabel: "Buscar por razão social",
  modeNameHint: "Pesquise a empresa pelo nome — em homologação.",
  modeNameUnavailableTitle: "Busca por razão social em homologação",
  modeNameUnavailableMessage:
    "A pesquisa nominal depende de um provedor externo ainda em homologação. Enquanto isso, consulte por CNPJ ou preencha manualmente.",
  modeManualLabel: "Preencher manualmente",
  modeManualHint:
    "Abra o formulário e informe os dados — sem depender de consulta externa.",

  modeSwitchConfirm:
    "Trocar a forma de início descarta a consulta assistida em andamento. Os dados já preenchidos no formulário são mantidos. Continuar?",

  cnpjInputLabel: "CNPJ do fornecedor",
  cnpjInputPlaceholder: "00.000.000/0000-00",
  cnpjInvalid: "Informe um CNPJ válido (14 dígitos com verificadores).",
  consultAction: "Consultar dados cadastrais",
  consultingAction: "Consultando…",
  newConsultAction: "Nova consulta",

  duplicateClearTitle: "Nenhuma correspondência exata encontrada",
  duplicateClearMessage:
    "A consulta por documento exato não localizou fornecedor com este CNPJ no cadastro. Isso não é garantia definitiva — a validação final ocorre no envio.",
  duplicatePossibleTitle: "Este CNPJ já possui cadastro no Protheus",
  duplicatePossibleMessage:
    "Encontramos registros vinculados a este CNPJ. Confira se algum deles atende à sua necessidade antes de continuar.",
  duplicatePossibleFooter:
    "Você pode continuar o preenchimento normalmente.",
  duplicateInconclusiveTitle: "Verificação de duplicidade não concluída",
  duplicateInconclusiveMessage:
    "Não foi possível consultar o cadastro interno agora. Isso não significa que o fornecedor não exista — você pode continuar o preenchimento e conferir depois.",
  duplicateMatchColumn: "Fornecedor",
  duplicateMatchBlocked: "Bloqueado",
  duplicateOpenMatch: "Conferir cadastro",
  existingSuppliersPageLoadError:
    "Não foi possível carregar esta página de cadastros. Tente novamente — seu formulário não foi alterado.",
  existingSuppliersEmptyPage:
    "Nenhum registro nesta página. Volte para a página anterior.",

  identityReplaceConfirm:
    "A identidade do fornecedor no formulário será alterada: o CNPJ será substituído pelo documento consultado e o tipo de pessoa ajustado para Pessoa Jurídica. Confirmar a substituição?",
  identityReplaceConfirmWithFields:
    "A identidade do fornecedor no formulário será alterada: o CNPJ será substituído pelo documento consultado e o tipo de pessoa ajustado para Pessoa Jurídica. Campos já preenchidos podem pertencer a outra empresa — revise-os antes de aplicar novas sugestões. Confirmar a substituição?",
  identityBlockedTitle: "Sugestões de outro CNPJ",
  identityBlockedMessage:
    "As sugestões abaixo pertencem ao CNPJ consultado, diferente do documento atual no formulário. Elas não podem ser aplicadas até que a identidade seja confirmada.",
  identityConfirmAction: "Usar CNPJ consultado no formulário",

  suggestionsTitle: "Sugestões de preenchimento",
  suggestionsDescription:
    "Dados de fonte externa pública. Nada é aplicado sozinho — confirme campo a campo ou aplique as elegíveis.",
  applyOneAction: "Aplicar",
  applyAllAction: "Aplicar sugestões elegíveis",
  overwriteConfirm:
    "O campo já possui valor informado. Substituir pela sugestão externa?",
  statusSuggested: "Sugestão",
  statusConfirmed: "Aplicado",
  statusChanged: "Editado",
  statusUnavailable: "Indisponível na fonte",
  reviewManually: "Verificar manualmente — equivalência não garantida",
  fieldLabelFallback: "Campo",
  currentValueLabel: "Valor atual no formulário",
  sourceLabel: "Fonte",
  retrievedLabel: "Consultado em",
  noSuggestionsTitle: "Nenhuma sugestão retornada",
  noSuggestionsMessage:
    "A consulta respondeu sem dados aplicáveis ao formulário. Preencha manualmente.",
  manualContinueHint:
    "Se a consulta falhar, o preenchimento manual continua disponível normalmente.",

  errorInvalid: "CNPJ inválido — confira os dígitos informados.",
  errorNotFound: "CNPJ não localizado na base pública consultada.",
  errorForbidden: "Sem permissão para consultar dados cadastrais externos.",
  errorRateLimited:
    "Limite de consultas atingido. Aguarde e tente novamente.",
  errorUnavailable:
    "Serviço de dados externos indisponível no momento. Você pode continuar preenchendo manualmente.",
  errorNetwork:
    "Falha de comunicação. Verifique a conexão e tente novamente.",
} as const;

/**
 * S9.B/S9.C — formatadores compartilhados do bounded context suppliers.
 * Fonte canônica em `../externalSourceFormat` (reuso E14 enriquecimento,
 * S9.R1); re-export preserva os consumidores do fluxo assistido.
 */
export {
  PORTAL_TIME_ZONE,
  PORTAL_TIME_ZONE_LABEL,
  formatRetrievedAt,
  providerDisplayName,
} from "../externalSourceFormat";

export function mapCreationPreviewError(err: unknown): string {
  if (err instanceof ApiRequestError) {
    if (err.status === 429) {
      return err.retryAfter
        ? `${CREATION_CONTENT.errorRateLimited} Tente em ${err.retryAfter}s.`
        : CREATION_CONTENT.errorRateLimited;
    }
    if (err.status === 401 || err.status === 403) {
      return CREATION_CONTENT.errorForbidden;
    }
    if (err.status === 404) return CREATION_CONTENT.errorNotFound;
    if (err.status === 422 || err.status === 400) {
      return CREATION_CONTENT.errorInvalid;
    }
    if (err.status === 502 || err.status === 503 || err.status === 504) {
      return CREATION_CONTENT.errorUnavailable;
    }
  }
  return CREATION_CONTENT.errorNetwork;
}
