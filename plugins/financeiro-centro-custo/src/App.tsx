import { configureHttpClient } from "./api/httpClient";
import { DespesasCentroCustoPage } from "./app/DespesasCentroCustoPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return <DespesasCentroCustoPage />;
}
