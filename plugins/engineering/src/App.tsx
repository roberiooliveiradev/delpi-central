import { useEffect } from "react";

import { configureHttpClient } from "./api/httpClient";
import { HomePage } from "./pages/HomePage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  search?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

export default function App({ getAccessToken }: AppProps) {
  useEffect(() => {
    if (getAccessToken) configureHttpClient(getAccessToken);
  }, [getAccessToken]);

  return <HomePage />;
}
