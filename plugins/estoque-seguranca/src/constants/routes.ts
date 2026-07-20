export const ESS_ROUTES = {
  home: "/apps/estoque-seguranca",
  consumptionAnalysis: "/apps/estoque-seguranca/analise-consumo",
} as const;

export function normalizeEssPath(pathname: string): string {
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}
