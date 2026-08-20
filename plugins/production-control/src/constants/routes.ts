export const PPC_BASE_PATH = "/apps/production-control";
export const PPC_API_BASE = "/apps/production-control-api";
export const DEFAULT_BRANCH = "01";
export const BRANCH_STORAGE_KEY = "production-control.branch";

export const DEFAULT_SUBPLUGIN = "home";

export const PPC_ROUTES = {
  home: PPC_BASE_PATH,
  problemAnalysis: `${PPC_BASE_PATH}/problem-analysis`,
} as const;
