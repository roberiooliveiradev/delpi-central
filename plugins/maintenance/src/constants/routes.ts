export const MAINTENANCE_ROUTES = {
  home: "/apps/maintenance",
  filialHome: (filial: string) => `/apps/maintenance/filial-${filial}`,
  filiais: "/apps/maintenance/filiais",
  manutencaoGeral: (filial = "01") => `/apps/maintenance/filial-${filial}/manutencao-geral`,
  /** @deprecated Caminho legado — mantido para bookmarks antigos. */
  manutencaoGeralLegacy: "/apps/maintenance/manutencao-geral",
  miniAplicadores: "/apps/maintenance/mini-aplicadores",
  miniAplicadoresRelatorio: "/apps/maintenance/mini-aplicadores/relatorio",
  miniAplicadoresConfiguracao: "/apps/maintenance/mini-aplicadores/configuracao",
  miniAplicadorDetail: (codigo: string) =>
    `/apps/maintenance/mini-aplicadores/${encodeURIComponent(codigo)}`,
} as const;

/** @deprecated Use miniAplicadoresRelatorio */
export const LEGACY_RELATORIO_ROUTE = "/apps/maintenance/relatorio";

/** @deprecated Use miniAplicadoresConfiguracao */
export const LEGACY_CONFIGURACAO_ROUTE = "/apps/maintenance/configuracao";
