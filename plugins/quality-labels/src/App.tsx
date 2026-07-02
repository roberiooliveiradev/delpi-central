import { configureHttpClient } from "./api/httpClient";
import { QualityLabelsAdminPage } from "./pages/QualityLabelsAdminPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return <QualityLabelsAdminPage />;
}
