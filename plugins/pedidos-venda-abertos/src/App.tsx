import { configureHttpClient } from "./api/httpClient";
import { PedidosVendaAbertosPage } from "./pages/PedidosVendaAbertosPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return <PedidosVendaAbertosPage />;
}
