export const ENGINEERING_BASE_PATH = "/apps/dashboard-engineering";

export const ENGINEERING_ROUTES = {
  home: ENGINEERING_BASE_PATH,
  lmp: `${ENGINEERING_BASE_PATH}/lmp`,
  transforma: `${ENGINEERING_BASE_PATH}/transforma`,
} as const;
