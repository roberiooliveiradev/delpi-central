/** Chave do recorte corrente. Não é entidade de domínio. */
export function dashboardRequestKey(input: {
  params: Record<string, string>;
  siParams: Record<string, string>;
  granularity: string;
  reloadNonce: number;
}): string {
  return JSON.stringify(input);
}

/** Resposta antiga não pode sobrescrever um recorte mais novo. */
export function shouldCommitDashboardRequest(startedKey: string, latestKey: string): boolean {
  return startedKey === latestKey;
}

/** Refresh visível no mesmo render em que o recorte muda, antes do fetch resolver. */
export function isDashboardRefreshing(
  hasAuthoritativeContent: boolean,
  settledKey: string | null,
  requestKey: string,
): boolean {
  return hasAuthoritativeContent && settledKey !== requestKey;
}
