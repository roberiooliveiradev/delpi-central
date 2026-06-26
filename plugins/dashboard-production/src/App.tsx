import { useEffect } from "react";

import { configureHttpClient } from "./api/httpClient";
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

function renderPage(path: string) {
  const route = parseProductionPath(path);

  if (route.view === "oee-detail" && route.appointmentId) {
    return (
      <OeeAppointmentDetailPage
        appointmentId={route.appointmentId}
        branch={readAppointmentBranchFromUrl()}
        pathname={path}
      />
    );
  }

  if (route.view === "otd-detail" && route.productionOrder) {
    return (
      <OtdOrderDetailPage
        productionOrder={route.productionOrder}
        branch={readOrderBranchFromUrl()}
        productType={readOrderProductTypeFromUrl()}
        pathname={path}
      />
    );
  }

  if (route.view === "oee") {
    return <OeePage pathname={path} />;
  }

  if (route.view === "otd") {
    return <OtdPage pathname={path} />;
  }

  return <DashboardProductionPage pathname={path} />;
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useProductionRouterPath(pathnameFromHost);
  const path = normalizeProductionPath(pathname);

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
    <div className="dp-app-shell" key={path}>
      {renderPage(path)}
    </div>
  );
}
