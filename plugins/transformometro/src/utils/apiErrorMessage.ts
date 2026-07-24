/**
 * Mensagens de erro HTTP do client Transformômetro — uma fonte para o usuário.
 * Não menciona migrations internas nem códigos sem contexto.
 */

export function describeHttpError(
  status: number,
  detail?: string | null,
): string {
  const trimmed = typeof detail === "string" ? detail.trim() : "";
  if (trimmed && status >= 400 && status < 500 && status !== 429) {
    return trimmed;
  }

  switch (status) {
    case 401:
      return "Sessão expirada ou não autenticada. Faça login novamente.";
    case 403:
      return "Você não tem permissão para esta operação.";
    case 404:
      return "Registro não encontrado. Ele pode ter sido excluído ou você não tem acesso.";
    case 409:
      return trimmed || "Conflito ao salvar. Recarregue a tela e tente novamente.";
    case 422:
      return trimmed || "Dados inválidos. Verifique os campos e tente novamente.";
    case 429:
      return "Muitas requisições em pouco tempo. Aguarde alguns segundos e tente novamente.";
    case 502:
    case 503:
    case 504:
      return "A API do Transformômetro está temporariamente indisponível. Tente novamente em instantes.";
    default:
      break;
  }

  if (status >= 500) {
    return "Falha interna na API do Transformômetro. Tente novamente; se persistir, avise o suporte.";
  }

  return trimmed || `Falha na requisição (HTTP ${status}).`;
}

/** Título curto para painel de erro (StateBoxPanel), separado do detalhe. */
export function describeHttpErrorTitle(status: number): string {
  if (status === 401 || status === 403) return "Acesso negado";
  if (status === 404) return "Não encontrado";
  if (status === 409 || status === 422) return "Não foi possível salvar";
  if (status === 429) return "Muitas requisições";
  if (status >= 500) return "Serviço indisponível";
  return "Não foi possível concluir";
}
