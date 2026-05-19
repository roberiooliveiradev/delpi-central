export const FINANCIAL_BASE_PATH = "/apps/dashboard-financial";

export const FINANCIAL_ROUTES = {
  home: FINANCIAL_BASE_PATH,
  rol: `${FINANCIAL_BASE_PATH}/rol`,
  ebitda: `${FINANCIAL_BASE_PATH}/ebitda`,
  fixedCost: `${FINANCIAL_BASE_PATH}/fixed-cost`,
  pmr: `${FINANCIAL_BASE_PATH}/pmr`,
} as const;
