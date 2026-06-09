export const CONSOLE_BASE = "/apps/api-delpi-console";

export const CONSOLE_ROUTES = {
  home: CONSOLE_BASE,
  documentacao: `${CONSOLE_BASE}/documentacao`,
  verificacoes: `${CONSOLE_BASE}/verificacoes`,
  sql: `${CONSOLE_BASE}/sql`,
  explorer: `${CONSOLE_BASE}/explorer`,
  spec: `${CONSOLE_BASE}/spec`,
  history: `${CONSOLE_BASE}/history`,
} as const;

export const API_DELPI_DOCS_URL = "/apps/api-delpi/docs";
export const API_DELPI_OPENAPI_URL = "/apps/api-delpi/openapi.json";
