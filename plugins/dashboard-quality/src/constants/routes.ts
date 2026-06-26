export const QUALITY_BASE_PATH = "/apps/dashboard-quality";

export const QUALITY_ROUTES = {
  home: QUALITY_BASE_PATH,
  ppm: `${QUALITY_BASE_PATH}/ppm`,
  ppmDetail: `${QUALITY_BASE_PATH}/ppm/detail`,
  nonconformities: `${QUALITY_BASE_PATH}/nonconformities`,
  nonconformityDetail: `${QUALITY_BASE_PATH}/nonconformities/detail`,
  kaizen: `${QUALITY_BASE_PATH}/kaizen`,
  audit5s: `${QUALITY_BASE_PATH}/audit-5s`,
} as const;

export function buildKaizenDetailPath(kaizenId: string): string {
  return `${QUALITY_ROUTES.kaizen}/${encodeURIComponent(kaizenId)}`;
}

export function buildPpmDetailPath(): string {
  return QUALITY_ROUTES.ppmDetail;
}

export function buildNonconformityDetailPath(): string {
  return QUALITY_ROUTES.nonconformityDetail;
}
