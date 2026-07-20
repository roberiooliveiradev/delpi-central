import { configureHttpClient } from "./api/httpClient";
import { ESS_ROUTES, normalizeEssPath } from "./constants/routes";
import { useEssRouterPath } from "./hooks/useEssRouterPath";
import { ConsumptionAnalysisPage } from "./pages/ConsumptionAnalysisPage";
import { SafetyStockPage } from "./pages/SafetyStockPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

function renderPage(path: string) {
  if (
    path === ESS_ROUTES.consumptionAnalysis ||
    path.startsWith(`${ESS_ROUTES.consumptionAnalysis}/`)
  ) {
    return <ConsumptionAnalysisPage />;
  }
  return <SafetyStockPage />;
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const pathname = useEssRouterPath(pathnameFromHost);
  const path = normalizeEssPath(pathname);

  return <div key={path}>{renderPage(path)}</div>;
}
