import { QUALITY_BASE_PATH, QUALITY_ROUTES } from "../constants/routes";

export type ParsedQualityRoute =
  | {
      view: "kaizen-detail";
      kaizenId: string;
    }
  | {
      view: "page";
      path: string;
    };

function normalizeQualityPath(pathname: string): string {
  if (!pathname) return QUALITY_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseQualityPath(pathname: string): ParsedQualityRoute {
  const path = normalizeQualityPath(pathname);
  const kaizenPrefix = `${QUALITY_ROUTES.kaizen}/`;

  if (path.startsWith(kaizenPrefix)) {
    const kaizenId = decodeURIComponent(path.slice(kaizenPrefix.length));
    if (kaizenId) {
      return {
        view: "kaizen-detail",
        kaizenId,
      };
    }
  }

  return {
    view: "page",
    path: path.startsWith(QUALITY_BASE_PATH) ? path : QUALITY_ROUTES.home,
  };
}
