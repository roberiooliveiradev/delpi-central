import { useEffect, useState } from "react";

import { configureHttpClient } from "./api/httpClient";
import { PRODUCTION_ROUTES } from "./constants/routes";
import { useProductionRouterPath } from "./hooks/useProductionRouterPath";
import { DashboardProductionPage } from "./pages/DashboardProductionPage";
import { OtdOrderDetailPage } from "./pages/OtdOrderDetailPage";
import { OtdPage } from "./pages/OtdPage";
import {
  normalizeProductionPath,
  parseProductionPath,
  readOrderBranchFromUrl,
  readOrderProductTypeFromUrl,
} from "./utils/routeParser";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useProductionRouterPath(pathnameFromHost);
  const path = normalizeProductionPath(pathname);
  const route = parseProductionPath(path);

  const showHome = route.view === "home";
  const showOtd = route.view === "otd";
  const showOtdDetail =
    route.view === "otd-detail" && Boolean(route.productionOrder);

  const [otdPageMounted, setOtdPageMounted] = useState(showOtd || showOtdDetail);

  useEffect(() => {
    if (showOtd || showOtdDetail) {
      setOtdPageMounted(true);
    }
  }, [showOtd, showOtdDetail]);

  useEffect(() => {
    if (typeof window === "undefined" || !("scrollRestoration" in window.history)) {
      return;
    }

    const previous = window.history.scrollRestoration;
    window.history.scrollRestoration = "auto";

    return () => {
      window.history.scrollRestoration = previous;
    };
  }, []);

  return (
    <div className="dp-app-shell">
      {showHome ? (
        <DashboardProductionPage pathname={pathnameFromHost ?? path} />
      ) : null}

      {otdPageMounted ? (
        <div hidden={!showOtd} aria-hidden={!showOtd}>
          <OtdPage pathname={PRODUCTION_ROUTES.otd} />
        </div>
      ) : null}

      {showOtdDetail && route.productionOrder ? (
        <OtdOrderDetailPage
          productionOrder={route.productionOrder}
          branch={readOrderBranchFromUrl()}
          productType={readOrderProductTypeFromUrl()}
          pathname={path}
        />
      ) : null}
    </div>
  );
}
