export const QUALITY_BASE_PATH = "/apps/dashboard-quality";

export const QUALITY_ROUTES = {
  home: QUALITY_BASE_PATH,
  ppm: `${QUALITY_BASE_PATH}/ppm`,
  nonconformities: `${QUALITY_BASE_PATH}/nonconformities`,
  kaizen: `${QUALITY_BASE_PATH}/kaizen`,
  audit5s: `${QUALITY_BASE_PATH}/audit-5s`,
} as const;

export function buildKaizenDetailPath(kaizenId: string): string {
  return `${QUALITY_ROUTES.kaizen}/${encodeURIComponent(kaizenId)}`;
}
