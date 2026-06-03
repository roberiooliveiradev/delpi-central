import { configureHttpClient } from "./api/httpClient";
import { SchedulingPage } from "./pages/SchedulingPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return <SchedulingPage pathname={pathname} />;
}
