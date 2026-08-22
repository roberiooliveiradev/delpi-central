export const FINANCIAL_BASE_PATH = "/apps/financial";
export const FINANCIAL_API_BASE = "/apps/financial-api";
export const DEFAULT_BRANCH = "01";
export const BRANCH_STORAGE_KEY = "financial.branch";

export const DEFAULT_SUBPLUGIN = "home";

export const FINANCIAL_ROUTES = {
  home: FINANCIAL_BASE_PATH,
  delinquency: `${FINANCIAL_BASE_PATH}/delinquency`,
  costCenters: `${FINANCIAL_BASE_PATH}/cost-centers`,
  indicators: `${FINANCIAL_BASE_PATH}/indicators`,
} as const;
