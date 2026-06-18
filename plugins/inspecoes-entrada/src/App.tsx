import { configureHttpClient } from "./api/httpClient";
import { FilialAppPage } from "./pages/FilialAppPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  search?: string;
};

export default function App({ getAccessToken, pathname, search }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return <FilialAppPage pathname={pathname} search={search} />;
}
