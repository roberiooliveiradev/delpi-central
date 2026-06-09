export const CONSOLE_BASE = "/apps/api-delpi-console";

export const CONSOLE_ROUTES = {
  home: CONSOLE_BASE,
  explorer: `${CONSOLE_BASE}/explorer`,
  swagger: `${CONSOLE_BASE}/swagger`,
  spec: `${CONSOLE_BASE}/spec`,
  history: `${CONSOLE_BASE}/history`,
} as const;

export const API_DELPI_SWAGGER_URL = "/apps/api-delpi/docs";
export const API_DELPI_OPENAPI_URL = "/apps/api-delpi/openapi.json";
