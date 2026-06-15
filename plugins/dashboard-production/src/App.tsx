import { useEffect, useState } from "react";

import { configureHttpClient } from "./api/httpClient";
import { PRODUCTION_ROUTES } from "./constants/routes";
import { useProductionRouterPath } from "./hooks/useProductionRouterPath";
import { DashboardProductionPage } from "./pages/DashboardProductionPage";
import { OeeAppointmentDetailPage } from "./pages/OeeAppointmentDetailPage";
import { OeePage } from "./pages/OeePage";
import { OtdOrderDetailPage } from "./pages/OtdOrderDetailPage";
import { OtdPage } from "./pages/OtdPage";
import {
  normalizeProductionPath,
  parseProductionPath,
  readAppointmentBranchFromUrl,
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
  const showOee = route.view === "oee";
  const showOeeDetail =
    route.view === "oee-detail" && Boolean(route.appointmentId);
  const showOtd = route.view === "otd";
  const showOtdDetail =
    route.view === "otd-detail" && Boolean(route.productionOrder);

  const [otdPageMounted, setOtdPageMounted] = useState(showOtd || showOtdDetail);
  const [oeePageMounted, setOeePageMounted] = useState(showOee || showOeeDetail);

  useEffect(() => {
    if (showOtd || showOtdDetail) {
      setOtdPageMounted(true);
    }
  }, [showOtd, showOtdDetail]);

  useEffect(() => {
    if (showOee || showOeeDetail) {
      setOeePageMounted(true);
    }
  }, [showOee, showOeeDetail]);

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

      {oeePageMounted ? (
        <div hidden={!showOee} aria-hidden={!showOee}>
          <OeePage pathname={PRODUCTION_ROUTES.oee} />
        </div>
      ) : null}

      {otdPageMounted ? (
        <div hidden={!showOtd} aria-hidden={!showOtd}>
          <OtdPage pathname={PRODUCTION_ROUTES.otd} />
        </div>
      ) : null}

      {showOeeDetail && route.appointmentId ? (
        <OeeAppointmentDetailPage
          appointmentId={route.appointmentId}
          branch={readAppointmentBranchFromUrl()}
          pathname={path}
        />
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
