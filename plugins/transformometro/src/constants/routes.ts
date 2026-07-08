export const TRANSFORMOMETRO_ROUTES = {
  home: "/apps/transformometro",
  dashboard: "/apps/transformometro/dashboard",
  processos: "/apps/transformometro/processos",
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
