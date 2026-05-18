export const QUALITY_BASE_PATH = "/apps/dashboard-quality";

export const QUALITY_ROUTES = {
  home: QUALITY_BASE_PATH,
  ppm: `${QUALITY_BASE_PATH}/ppm`,
} as const;
