import { configureHttpClient } from "./api/httpClient";
import { Audit5sPage } from "./pages/Audit5sPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  search?: string;
};

export default function App({ getAccessToken, pathname, search }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return <Audit5sPage pathname={pathname} search={search} />;
}
