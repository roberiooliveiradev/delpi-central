export const TRANSFORMOMETRO_ROUTES = {
  home: "/apps/transformometro",
  dashboard: "/apps/transformometro/dashboard",
  processos: "/apps/transformometro/processos",
  atas: "/apps/transformometro/atas",
  atasPending: "/apps/transformometro/atas/pending",
  minhaAssinatura: "/apps/transformometro/minha-assinatura",
  configuracoes: "/apps/transformometro/configuracoes",
  configuracoesUnidades: "/apps/transformometro/configuracoes/unidades",
  configuracoesDepartamentos: "/apps/transformometro/configuracoes/departamentos",
  configuracoesRecursos: "/apps/transformometro/configuracoes/recursos",
  /** @deprecated use configuracoesUnidades */
  filiais: "/apps/transformometro/configuracoes/unidades",
  /** @deprecated use configuracoesDepartamentos */
  setores: "/apps/transformometro/configuracoes/departamentos",
  /** @deprecated use configuracoesRecursos */
  recursos: "/apps/transformometro/configuracoes/recursos",
  dados: "/apps/transformometro/dados",
} as const;

export function buildAtaPath(ataId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.atas}/${ataId}`;
}

export function buildAtaEditPath(ataId: string): string {
  return `${buildAtaPath(ataId)}/edit`;
}

export function buildAtaSignPath(ataId: string): string {
  return `${buildAtaPath(ataId)}/sign`;
}
