import { configureHttpClient } from "./api/httpClient";
import { SafetyStockPage } from "./pages/SafetyStockPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return <SafetyStockPage />;
}
