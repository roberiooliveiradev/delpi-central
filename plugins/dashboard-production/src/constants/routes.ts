export const PRODUCTION_BASE_PATH = "/apps/dashboard-production";

export const PRODUCTION_ROUTES = {
  home: PRODUCTION_BASE_PATH,
  otd: `${PRODUCTION_BASE_PATH}/otd`,
} as const;
