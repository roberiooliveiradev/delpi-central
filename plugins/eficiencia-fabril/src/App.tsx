import { configureHttpClient } from "./api/httpClient";
import { useEficienciaFabrilRouterPath } from "./hooks/useEficienciaFabrilRouterPath";
import { DashboardEficienciaFabrilPage } from "./pages/DashboardEficienciaFabrilPage";
import { EficienciaFabrilAppointmentDetailPage } from "./pages/EficienciaFabrilAppointmentDetailPage";
import {
  parseEficienciaFabrilPath,
  readAppointmentBranchFromUrl,
} from "./utils/routeParser";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useEficienciaFabrilRouterPath(pathnameFromHost);
  const route = parseEficienciaFabrilPath(pathname);

  if (
    route.view === "appointment-detail" &&
    route.appointmentId &&
    route.branchRoute
  ) {
    return (
      <EficienciaFabrilAppointmentDetailPage
        appointmentId={route.appointmentId}
        branchRoute={route.branchRoute}
        branch={readAppointmentBranchFromUrl()}
      />
    );
  }

  return <DashboardEficienciaFabrilPage pathname={pathname} />;
}
