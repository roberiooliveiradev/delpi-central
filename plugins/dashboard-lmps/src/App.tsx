import { useEffect } from "react";
import { configureHttpClient } from "./api/httpClient";
import { DashboardLmpsPage } from "./pages/DashboardLmpsPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
};

export default function App({ getAccessToken }: AppProps) {
  useEffect(() => {
    configureHttpClient(() => getAccessToken?.());
  }, [getAccessToken]);

  return <DashboardLmpsPage />;
}