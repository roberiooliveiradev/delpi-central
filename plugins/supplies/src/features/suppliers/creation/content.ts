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
  duplicatePossibleTitle: "Possível fornecedor já cadastrado",
  duplicatePossibleMessage:
    "Existe registro com este documento exato no cadastro. Verifique antes de continuar — CNPJ não é chave única e o cadastro pode mudar até a confirmação.",
  duplicateInconclusiveTitle: "Verificação de duplicidade não concluída",
  duplicateInconclusiveMessage:
    "Não foi possível consultar o cadastro interno agora. Isso não significa que o fornecedor não exista — você pode continuar o preenchimento e conferir depois.",
  duplicateMatchColumn: "Fornecedor",
  duplicateMatchBlocked: "Bloqueado",
  duplicateOpenMatch: "Abrir ficha",

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

export function formatRetrievedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

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
