export const SUPPLIES_BASE_PATH = "/apps/dashboard-supplies";

export const SUPPLIES_ROUTES = {
  home: SUPPLIES_BASE_PATH,
  cpv: `${SUPPLIES_BASE_PATH}/cpv`,
  otd: `${SUPPLIES_BASE_PATH}/otd`,
  stock: `${SUPPLIES_BASE_PATH}/stock`,
  inventoryTurnover: `${SUPPLIES_BASE_PATH}/inventory-turnover`,
  negotiationSavings: `${SUPPLIES_BASE_PATH}/negotiation-savings`,
} as const;
