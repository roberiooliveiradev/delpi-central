/** DELPI-MYREQUESTS-ENGINEERING-INTEGRATION-ISOLATION-01 — gate da
 * integração My Requests ↔ Engineering API.
 *
 * Regra do owner de Engenharia: somente solicitações do tipo canônico
 * `raw-material-creation` integram com a Engineering API (casos PRC).
 * Qualquer outro tipo ou recorte de filial NÃO aciona a chamada —
 * a decisão vive aqui, num ponto único e testável, e nunca dispersa
 * em condicionais ad hoc.
 */

export const PRC_REQUEST_TYPE_CODE = "raw-material-creation";

/** Mensagem contextual de indisponibilidade da integração PRC.
 * Nunca interpola `err.message` — detalhes internos de backend
 * (ex.: falha de conexão SQL) não vazam para a UI. */
export const PRC_LIST_UNAVAILABLE_MESSAGE =
  "Cadastro de produtos e matérias-primas indisponível no momento. " +
  "Suas demais solicitações seguem listadas normalmente.";

export type PrcListGateFilters = {
  typeCode?: string;
  branch?: string;
};

/** Decide se a listagem unificada deve consultar a Engineering API.
 *
 * `true` apenas quando o recorte pedido pode conter casos PRC:
 * sem filtro de tipo ou filtro explícito ao tipo canônico, e sem
 * filtro de filial (o contrato PRC não possui filial — incluí-lo
 * produziria linhas desonestas). */
export function shouldIncludePrcInList(
  filters: PrcListGateFilters,
): boolean {
  return (
    (!filters.typeCode ||
      filters.typeCode === PRC_REQUEST_TYPE_CODE) &&
    !filters.branch
  );
}

/** Erro contextualizado da integração PRC — mensagem estática por
 * contrato; o detalhe técnico permanece no backend/log. */
export function prcListErrorMessage(): string {
  return PRC_LIST_UNAVAILABLE_MESSAGE;
}
