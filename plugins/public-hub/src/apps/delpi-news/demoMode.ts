/**
 * Gate da prova visual DELPI News (Etapa 1).
 *
 * Espelha o padrão de `plugins/delia/src/demo/demoMode.ts`:
 * a fixture só fica disponível em Vite DEV ou quando o bundle foi
 * construído deliberadamente com `VITE_DELPI_NEWS_DEMO=1` (homologação).
 *
 * Builds de produção do Docker (`vite build` sem a flag) nunca servem o mock.
 */

export type DelpiNewsDemoEnv = Pick<ImportMetaEnv, "DEV"> & {
  VITE_DELPI_NEWS_DEMO?: string;
};

/** Token de demonstração — não é credencial de produção nem canal real. */
export const DELPI_NEWS_DEMO_TOKEN = "demo";

/** Token legado da E1 inicial — rejeitado; não reativar em produção. */
export const DELPI_NEWS_LEGACY_OPEN_TOKEN = "aberto";

export const DELPI_NEWS_DEMO_BANNER =
  "DEMONSTRAÇÃO — conteúdo fictício para prova visual (não são notícias reais)";

export function isDelpiNewsDemoEnabled(env: DelpiNewsDemoEnv = import.meta.env): boolean {
  return Boolean(env.DEV) || env.VITE_DELPI_NEWS_DEMO === "1";
}
