import { configureHttpClient } from "./api/httpClient";
import { useProductionAppointmentsRouterPath } from "./hooks/useProductionAppointmentsRouterPath";
import { ProductionAppointmentsPage } from "./pages/ProductionAppointmentsPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useProductionAppointmentsRouterPath(pathnameFromHost);

  return <ProductionAppointmentsPage pathname={pathname} />;
}
