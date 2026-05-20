export const ENGINEERING_BASE_PATH = "/apps/dashboard-engineering";

export const LMP_DASHBOARD_PATH = "/apps/dashboard-lmps";

export const ENGINEERING_ROUTES = {
  home: ENGINEERING_BASE_PATH,
  processes: `${ENGINEERING_BASE_PATH}/processes`,
} as const;
